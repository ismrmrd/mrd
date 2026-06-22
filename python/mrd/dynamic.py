from __future__ import annotations

import functools
import inspect
import io
import json
import typing
from typing import Any, Callable, Optional

import numpy as np

from . import _binary
from . import types as _types
from .protocols import MrdReaderBase
from .types import Header, StreamItem

__all__ = [
    "DynamicMrdReader",
    "ModelRegistry",
    "SchemaInterpreter",
    "ByNameRecordSerializer",
    "UnknownUnionCase",
    "build_mrd_registry",
]


def _norm(name: str) -> str:
    """Normalize a schema identifier for matching.

    yardl changed its union-tag casing convention across versions (e.g. the
    StreamItem variant ``Acquisition`` became ``acquisition``); the variant
    identity is unchanged. Lowercasing absorbs that purely-cosmetic difference
    for both union tags and record field names. (Identifiers are unique
    case-insensitively, so this never collides.)
    """
    return name.lower()


class UnknownUnionCase:
    """Wrapper for a union variant present in the file but absent from the
    current model (e.g. a renamed/removed variant -- a genuine schema break,
    not just a casing difference). The payload is still decoded with the file's
    layout so the stream stays readable; the original schema ``tag`` is kept so
    callers can see what was skipped."""

    index = -1

    def __init__(self, tag: str, value: Any) -> None:
        self.tag = tag
        self.value = value

    def __repr__(self) -> str:
        return f"UnknownUnionCase(tag={self.tag!r})"


# ---------------------------------------------------------------------------
# A record serializer that reconciles by FIELD NAME instead of by position.
#
# The stock _binary.RecordSerializer reads fields positionally in the order it
# was constructed. That is correct only when the file's field order matches the
# model's. The dynamic path instead:
#   * decodes every field the FILE declares, in the FILE's order (keeps the
#     byte cursor aligned -- yardl's format is not self-delimiting per field),
#   * projects the decoded values onto the current model by name.
# Fields the current model dropped are decoded-and-discarded; fields the model
# added are simply never set, so ``construct`` (which calls the current class
# constructor) supplies their default -- ``None`` by invariant 3.
# ---------------------------------------------------------------------------
class ByNameRecordSerializer(_binary.TypeSerializer):
    def __init__(
        self,
        file_field_serializers: list[tuple[str, _binary.TypeSerializer]],
        field_name_map: dict[str, str],
        construct: Callable[..., Any],
    ) -> None:
        super().__init__(np.object_)
        # file (schema) field name -> serializer, in the file's declared order
        self._file_fields = file_field_serializers
        # normalized schema field name -> current model attribute name
        self._field_name_map = field_name_map
        self._construct = construct

    def read(self, stream: "_binary.CodedInputStream") -> Any:
        decoded: dict[str, Any] = {}
        for name, serializer in self._file_fields:
            value = serializer.read(stream)  # always decode, to stay aligned
            model_name = self._field_name_map.get(_norm(name))
            if model_name is not None:
                decoded[model_name] = value
            # else: field exists in file but not in current model -> discard
        return self._construct(**decoded)

    def read_numpy(self, stream: "_binary.CodedInputStream") -> Any:
        return self.read(stream)

    def write(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("ByNameRecordSerializer is read-only")

    def write_numpy(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("ByNameRecordSerializer is read-only")


# ---------------------------------------------------------------------------
# Map yardl primitive names to the shared runtime serializer singletons.
# ---------------------------------------------------------------------------
_PRIMITIVES: dict[str, _binary.TypeSerializer] = {
    "bool": _binary.bool_serializer,
    "int8": _binary.int8_serializer,
    "uint8": _binary.uint8_serializer,
    "int16": _binary.int16_serializer,
    "uint16": _binary.uint16_serializer,
    "int32": _binary.int32_serializer,
    "uint32": _binary.uint32_serializer,
    "int64": _binary.int64_serializer,
    "uint64": _binary.uint64_serializer,
    "size": _binary.size_serializer,
    "float32": _binary.float32_serializer,
    "float64": _binary.float64_serializer,
    "complexfloat32": _binary.complexfloat32_serializer,
    "complexfloat64": _binary.complexfloat64_serializer,
    "string": _binary.string_serializer,
    "date": _binary.date_serializer,
    "time": _binary.time_serializer,
    "datetime": _binary.datetime_serializer,
}


# ---------------------------------------------------------------------------
# Describes the CURRENT reader model: how to build each named type and which
# field/attribute names it declares. Built once from the current schema +
# generated ``mrd.types`` module by ``build_mrd_registry`` below.
# ---------------------------------------------------------------------------
class ModelRegistry:
    def __init__(self) -> None:
        # record name -> {schema field name (camelCase) -> model attribute name}
        self.record_field_map: dict[str, dict[str, str]] = {}
        # record name -> current constructor (called with **kwargs)
        self.record_construct: dict[str, Callable[..., Any]] = {}
        # union name -> (python union base type, {schema tag -> case class})
        self.unions: dict[str, tuple[type, dict[str, type]]] = {}
        # enum name -> python enum class
        self.enums: dict[str, type] = {}


def _strip_namespace(name: str) -> str:
    """``"Mrd.Header"`` -> ``"Header"``; primitives/type-params pass through."""
    return name.rsplit(".", 1)[-1]


def _init_param_names(cls: type) -> list[str]:
    """The keyword-only constructor parameter names of a generated record."""
    params = inspect.signature(cls.__init__).parameters
    return [
        n
        for n, p in params.items()
        if n != "self"
        and p.kind in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]


def build_mrd_registry() -> ModelRegistry:
    """Populate a :class:`ModelRegistry` from the *current* MRD schema and the
    generated ``mrd.types`` classes.

    The current schema's field order and the current constructor's parameter
    order are identical (yardl emits them together), so zipping them yields an
    exact ``schema-field-name -> model-attribute-name`` map without having to
    reimplement yardl's camelCase->snake_case rule. Invariant 2 (no renames)
    means this map is valid for older files too.
    """
    reg = ModelRegistry()
    schema = json.loads(MrdReaderBase.schema)
    for tdef in schema.get("types") or []:
        if not isinstance(tdef, dict) or "name" not in tdef:
            continue
        name = tdef["name"]
        cls = getattr(_types, name, None)

        # Record (possibly generic, e.g. Image / NdArray / Waveform)
        if "fields" in tdef:
            if cls is None:
                continue
            schema_field_names = [f["name"] for f in tdef["fields"]]
            model_attr_names = _init_param_names(cls)
            if len(schema_field_names) == len(model_attr_names):
                reg.record_field_map[name] = {
                    _norm(s): m for s, m in zip(schema_field_names, model_attr_names)
                }
            else:
                # Defensive: fall back to identity if shapes ever diverge.
                reg.record_field_map[name] = {
                    _norm(n): n for n in schema_field_names
                }
            reg.record_construct[name] = cls
            continue

        # Enum
        if "values" in tdef:
            if cls is not None:
                reg.enums[name] = cls
            continue

        # Union (tagged): its ``type`` is a list of {"tag":..., "type":...}
        inner = tdef.get("type")
        if isinstance(inner, list) and cls is not None:
            tag_map: dict[str, type] = {}
            for attr in vars(cls).values():
                tag = getattr(attr, "tag", None)
                if inspect.isclass(attr) and isinstance(tag, str):
                    tag_map[_norm(tag)] = attr
            if tag_map:
                reg.unions[name] = (cls, tag_map)

    return reg


# ---------------------------------------------------------------------------
# The interpreter: turn a schema JSON type-node into a runtime serializer,
# composing the SAME _binary.* classes the generated code composes, so
# per-record decode performance is identical to generated code. The only added
# cost is building the serializer tree once at open time.
# ---------------------------------------------------------------------------
class SchemaInterpreter:
    def __init__(self, file_schema: dict[str, Any], model: ModelRegistry) -> None:
        self._model = model
        self._file_types: dict[str, dict[str, Any]] = {}
        for t in file_schema.get("types") or []:
            if isinstance(t, dict) and "name" in t:
                self._file_types[t["name"]] = t
        # cache for non-generic named serializers and generic instantiations
        self._cache: dict[str, _binary.TypeSerializer] = {}
        # (union type name, schema tag) for variants present in the file but
        # absent from the current model -- genuine schema breaks, surfaced as
        # UnknownUnionCase rather than crashing the read.
        self.unmatched_variants: list[tuple[str, str]] = []

    # env maps a generic type-parameter name (e.g. "T") to its resolved
    # serializer, threaded through nested generic instantiations.
    def build(
        self, node: Any, env: Optional[dict[str, _binary.TypeSerializer]] = None
    ) -> _binary.TypeSerializer:
        env = env or {}

        if isinstance(node, str):
            if node in env:  # a generic type parameter
                return env[node]
            stripped = _strip_namespace(node)
            if stripped in _PRIMITIVES:
                return _PRIMITIVES[stripped]
            return self._build_named(stripped, env)

        if isinstance(node, list):
            return self._build_list(node, env)

        if not isinstance(node, dict):
            raise ValueError(f"Unexpected schema node: {node!r}")

        # Generic instantiation: {"name": "Mrd.Image", "typeArguments": [...]}
        if "typeArguments" in node:
            base = _strip_namespace(node["name"])
            args = [self.build(a, env) for a in node["typeArguments"]]
            return self._build_generic(base, args, env)

        if "stream" in node:
            return _binary.StreamSerializer(self.build(node["stream"]["items"], env))

        if "vector" in node:
            v = node["vector"]
            inner = self.build(v["items"], env)
            if v.get("length") is not None:
                return _binary.FixedVectorSerializer(inner, v["length"])
            return _binary.VectorSerializer(inner)

        if "array" in node:
            return self._build_array(node["array"], env)

        if "map" in node:
            m = node["map"]
            return _binary.MapSerializer(
                self.build(m["keys"], env), self.build(m["values"], env)
            )

        if "optional" in node:
            return _binary.OptionalSerializer(self.build(node["optional"], env))

        # Alias wrapper: {"name": X, "type": <other>}
        if "type" in node:
            return self.build(node["type"], env)

        raise ValueError(f"Unsupported schema node keys: {sorted(node.keys())}")

    def _build_list(
        self, node: list, env: dict[str, _binary.TypeSerializer]
    ) -> _binary.TypeSerializer:
        has_null = any(e is None or e == "null" for e in node)
        non_null = [e for e in node if e is not None and e != "null"]
        # T?  is encoded as a 2-element [null, T] -> Optional
        if has_null and len(non_null) == 1:
            return _binary.OptionalSerializer(self.build(non_null[0], env))
        # Anonymous (inline) unions don't occur in the MRD schema -- every union
        # is a named type, resolved via _build_named, where the python union
        # base class is known. Surface anything else clearly.
        raise NotImplementedError(
            "Anonymous union types are not supported by the dynamic reader; "
            f"got {node!r}"
        )

    def _build_array(
        self, arr: dict[str, Any], env: dict[str, _binary.TypeSerializer]
    ) -> _binary.TypeSerializer:
        inner = self.build(arr["items"], env)
        dims = arr.get("dimensions")
        if dims is None:
            # no/None dimensions -> dynamic-rank array
            return _binary.DynamicNDArraySerializer(inner)
        if isinstance(dims, int):
            # just a rank
            return _binary.NDArraySerializer(inner, dims)
        lengths = [d.get("length") for d in dims]
        if all(l is not None for l in lengths):
            return _binary.FixedNDArraySerializer(inner, tuple(lengths))
        return _binary.NDArraySerializer(inner, len(dims))

    def _build_union(
        self,
        name: str,
        cases: list[Any],
        env: dict[str, _binary.TypeSerializer],
    ) -> _binary.TypeSerializer:
        if name not in self._model.unions:
            raise ValueError(f"No model union registered for type '{name}'")
        union_type, tag_map = self._model.unions[name]
        case_specs: list[Optional[tuple[type, _binary.TypeSerializer]]] = []
        # Build cases in the FILE's order. Append-only (invariant 1) guarantees
        # the file's order is a prefix of the model's, so tag bytes line up.
        for c in cases:
            if c is None or c == "null":
                case_specs.append(None)
                continue
            tag = c.get("tag") if isinstance(c, dict) else None
            node = c["type"] if isinstance(c, dict) and "type" in c else c
            serializer = self.build(node, env)
            case_cls = tag_map.get(_norm(tag)) if tag is not None else None
            if case_cls is None:
                # Variant exists in the file but not in the current model
                # (renamed/removed). Decode its payload with the file layout so
                # the cursor stays aligned, but wrap it opaquely.
                self.unmatched_variants.append((name, str(tag)))
                factory = functools.partial(UnknownUnionCase, str(tag))
                case_specs.append((factory, serializer))
            else:
                case_specs.append((case_cls, serializer))
        return _binary.UnionSerializer(union_type, case_specs)

    def _build_named(
        self, name: str, env: dict[str, _binary.TypeSerializer]
    ) -> _binary.TypeSerializer:
        if name in self._cache:
            return self._cache[name]

        file_def = self._file_types.get(name)
        if file_def is None:
            raise ValueError(f"Unknown type referenced in schema: {name}")

        # Enum
        if "values" in file_def:
            base = file_def.get("base", "int32")
            base_ser = _PRIMITIVES.get(base, _binary.int32_serializer)
            enum_cls = self._model.enums.get(name)
            if enum_cls is None:
                raise ValueError(f"No model enum registered for '{name}'")
            ser: _binary.TypeSerializer = _binary.EnumSerializer(base_ser, enum_cls)
            self._cache[name] = ser
            return ser

        # Record (non-generic; generic records are reached via _build_generic)
        if "fields" in file_def:
            ser = self._build_record(name, file_def["fields"], env)
            self._cache[name] = ser
            return ser

        inner = file_def.get("type")

        # Union expressed as a named type (its ``type`` is a list)
        if isinstance(inner, list):
            ser = self._build_union(name, inner, env)
            self._cache[name] = ser
            return ser

        # Alias: {"name": X, "type": <other>}
        if inner is not None:
            ser = self.build(inner, env)
            self._cache[name] = ser
            return ser

        raise ValueError(f"Unsupported named type definition: {name}")

    def _build_record(
        self,
        model_name: str,
        fields: list[dict[str, Any]],
        env: dict[str, _binary.TypeSerializer],
        cache_key: Optional[str] = None,
    ) -> _binary.TypeSerializer:
        field_name_map = self._model.record_field_map.get(
            model_name, {_norm(f["name"]): f["name"] for f in fields}
        )
        construct = self._model.record_construct.get(model_name, dict)
        # Create the serializer first and cache it *before* building its field
        # serializers, so self-referential records terminate.
        ser = ByNameRecordSerializer([], field_name_map, construct)
        if cache_key is not None:
            self._cache[cache_key] = ser
        ser._file_fields = [
            (f["name"], self.build(f["type"], env)) for f in fields
        ]
        return ser

    def _build_generic(
        self,
        base: str,
        args: list[_binary.TypeSerializer],
        env: dict[str, _binary.TypeSerializer],
    ) -> _binary.TypeSerializer:
        gdef = self._file_types.get(base)
        if gdef is None:
            raise ValueError(f"Unknown generic type referenced in schema: {base}")
        params = gdef.get("typeParameters") or []
        child_env = dict(env)
        for p, a in zip(params, args):
            child_env[p] = a

        cache_key = base + "<" + ",".join(type(a).__name__ for a in args) + ">"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generic record (Image / NdArray / Waveform): build by name in child_env
        if "fields" in gdef:
            return self._build_record(
                base, gdef["fields"], child_env, cache_key=cache_key
            )
        # Generic array/alias (Array / ImageData / WaveformSamples): the body is
        # a plain type node parameterized by the type variable.
        inner = gdef.get("type")
        if inner is not None:
            ser = self.build(inner, child_env)
            self._cache[cache_key] = ser
            return ser
        raise ValueError(f"Unsupported generic type definition: {base}")


# ---------------------------------------------------------------------------
# The reader. Opens with expected_schema=None (bypassing the strict check),
# reads the file's embedded schema, verifies the protocol steps line up (the
# one fatal check), and builds a serializer per step from the embedded schema.
#
# It conforms to MrdReaderBase, so it is a drop-in for BinaryMrdReader:
# read_header()/read_data()/copy_to()/the context-manager protocol all work.
# ---------------------------------------------------------------------------
_CURRENT_PROTOCOL_STEPS = [
    s["name"] for s in json.loads(MrdReaderBase.schema)["protocol"]["sequence"]
]

# Built lazily so importing this module is cheap and failures surface on use.
_MRD_REGISTRY: Optional[ModelRegistry] = None


def _registry() -> ModelRegistry:
    global _MRD_REGISTRY
    if _MRD_REGISTRY is None:
        _MRD_REGISTRY = build_mrd_registry()
    return _MRD_REGISTRY


class DynamicMrdReader(_binary.BinaryProtocolReader, MrdReaderBase):
    """A schema-tolerant reader for the Mrd protocol.

    Unlike :class:`mrd.BinaryMrdReader`, this builds its serializers from the
    schema embedded in the file and reconciles decoded values onto the current
    model by field name, so it can read files written by an older (but
    backward-compatible) version of the library. The embedded schema is
    available on :attr:`embedded_schema`.
    """

    def __init__(
        self,
        stream: typing.Union[io.BufferedReader, io.BytesIO, typing.BinaryIO, str],
        skip_completed_check: bool = False,
    ) -> None:
        MrdReaderBase.__init__(self, skip_completed_check)
        # expected_schema=None -> skip the schema check
        _binary.BinaryProtocolReader.__init__(self, stream, None)

        file_schema = json.loads(self._schema)
        protocol = file_schema["protocol"]
        file_steps = [s["name"] for s in protocol["sequence"]]
        print("file_steps", file_steps)
        # FATAL CHECK: backward compatibility requires the file's protocol steps
        # to be a prefix of the current model's steps, in the same order
        # (invariant 4). Anything else means the byte framing can't be trusted.
        if file_steps != _CURRENT_PROTOCOL_STEPS[: len(file_steps)]:
            raise RuntimeError(
                "Incompatible protocol steps between file and reader.\n"
                f"  file:  {file_steps}\n  model: {_CURRENT_PROTOCOL_STEPS}"
            )

        interp = SchemaInterpreter(file_schema, _registry())
        step_serializers = {
            s["name"]: interp.build(s["type"]) for s in protocol["sequence"]
        }
        self._header_serializer = step_serializers["header"]
        self._data_serializer = step_serializers["data"]
        # union variants in the file with no current-model equivalent; if the
        # stream contains one it is yielded as an UnknownUnionCase.
        self.unmatched_variants = interp.unmatched_variants

    def _read_header(self) -> typing.Optional[Header]:
        return self._header_serializer.read(self._stream)

    def _read_data(self) -> typing.Iterable[StreamItem]:
        return self._data_serializer.read(self._stream)

    @property
    def embedded_schema(self) -> str:
        """The schema JSON string that was embedded in the file."""
        return self._schema

    @property
    def schema_matches(self) -> bool:
        """Whether the embedded schema matches this library's compiled-in schema."""
        return self._schema == MrdReaderBase.schema
