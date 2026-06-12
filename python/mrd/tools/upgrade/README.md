# `mrd-upgrade` — MRD Binary File Upgrade Tool

## Problem

MRD binary files are encoded using the [Yardl](https://github.com/microsoft/yardl) binary
format, which embeds the full schema JSON in every file. The reader validates that the
embedded schema exactly matches the one compiled into the current library, so files written
with an older version of the library are rejected by a newer one.

## Why a schema header swap is not enough

A naïve fix that patches the 21 KB schema string in-place while leaving the data bytes
unchanged only works when every record's binary layout is identical between versions. For
v2.2.0 → v2.2.1 that is not the case: three structural changes were made that affect the
on-disk layout, so the data section must be fully decoded and re-encoded.

## Schema changes: v2.2.0 → v2.2.1

### 1. New field in `AcquisitionHeader`

`acquisitionCenterFrequency: uint64?` was inserted at **field index 4** (between
`scanCounter` and `acquisitionTimeStampNs`). All subsequent field byte offsets shift.
A v2.2.0 file has 19 fields; v2.2.1 has 20.

### 2. New field in `Acquisition`

`phase: AcquisitionPhase?` was inserted at **field index 2** (between `data` and
`trajectory`). A v2.2.0 `Acquisition` has 3 fields; v2.2.1 has 4.

### 3. New `AcquisitionPrototype` variant in `StreamItem`

`AcquisitionPrototype` was inserted at **union tag index 1**, shifting every subsequent
variant's tag byte up by 1:

| Tag | v2.2.0              | v2.2.1                           |
|-----|---------------------|----------------------------------|
| 0   | Acquisition         | Acquisition *(unchanged)*        |
| 1   | WaveformUint32      | **AcquisitionPrototype** *(new)* |
| 2   | ImageUint16         | WaveformUint32                   |
| 3   | ImageInt16          | ImageUint16                      |
| 4   | ImageUint32         | ImageInt16                       |
| 5   | ImageInt32          | ImageUint32                      |
| 6   | ImageFloat          | ImageInt32                       |
| 7   | ImageDouble         | ImageFloat                       |
| 8   | ImageComplexFloat   | ImageDouble                      |
| 9   | ImageComplexDouble  | ImageComplexFloat                |
| 10  | AcquisitionBucket   | ImageComplexDouble               |
| 11  | ReconData           | AcquisitionBucket                |
| 12  | ArrayComplexFloat   | ReconData                        |
| 13  | ImageArray          | ArrayComplexFloat                |
| —   | *(absent)*          | ImageArray (14)                  |
| —   | *(absent)*          | Pulseq types (15–21)             |

`ReconBuffer` is also affected by change #1 because it contains an `NDArray` of
`AcquisitionHeader` objects.

## Approach

A key observation: `git diff v2.2.0 v2.2.1 -- python/mrd/` shows that `_binary.py` and
`yardl_types.py` are **byte-for-byte identical** between the two versions. Only the
Yardl-generated files changed. This means the current codec can decode old files
without modification, provided the serializers are configured with the v2.2.0 field
layouts.

The strategy is: **read with v2.2.0 serializer layouts → produce v2.2.1 objects → write
normally**. No old version of the library needs to be installed.

Two relevant Yardl internals make this clean:

- **Union tag bytes.** `UnionSerializer` encodes a variant as a single byte equal to its
  0-based position in the `cases` list passed to its constructor. By building a
  `UnionSerializer` whose `cases` list is in v2.2.0 tag order but uses v2.2.1
  `StreamItem.*` subclasses, decoded objects carry the correct v2.2.1 `.index` values and
  write out with the correct v2.2.1 tag bytes automatically — no explicit tag remapping.

- **Schema validation bypass.** `BinaryProtocolReader.__init__` rejects files with a
  mismatched schema. Passing `expected_schema=None` disables this check, allowing
  `V220MrdReader` to open v2.2.0 files using the current `_binary.py` infrastructure.

## Implementation

All upgrade logic lives in this directory (`python/mrd/tools/upgrade/`):

**`_schema_registry.py`** — embeds the v2.2.0 schema string as a raw literal alongside a
reference to the current v2.2.1 schema. `identify_file_version(path)` reads the
varint-prefixed schema string from the file header and returns a version string or `None`.

**`_v220_reader.py`** — read-only serializers matching the v2.2.0 on-disk layout that
produce v2.2.1 objects, injecting `None` for the two new optional fields.
`_build_v220_stream_item_union()` constructs the 14-case union with v2.2.0 tag ordering.
`V220MrdReader` wraps these with `expected_schema=None`.

**`__init__.py`** — CLI entry point (`mrd-upgrade`) and public API
(`upgrade_mrd_file(src, dst)`). Detects the source version, raises `ValueError` for
unknown/unsupported/already-current files, then walks the chain in `_SUPPORTED_UPGRADES`
step-by-step (with intermediate temp files when more than one step is needed). The final
result is always staged in a sibling `tempfile.mkstemp` and atomically `os.replace`d
into `dst`, so partial output is never observable — this also makes `src == dst` safe and
is what `--in-place` relies on.

**`__main__.py`** — thin shim so `python -m mrd.tools.upgrade` invokes `main()`.

## Testing

Tests in `test/upgrade/` are self-contained — no pre-existing MRD data files are required.
`test-upgrade.sh`:

1. Extracts the entire `python/mrd/` tree from the `v2.2.0` git tag via `git archive`
   into a temp directory. Setting `PYTHONPATH` to that directory shadows the installed
   package — no separate virtualenv or PyPI install.
2. Runs `generate_v220.py` under those v2.2.0 codecs to produce a genuine v2.2.0 stream
   exercising 12 of the 14 `StreamItem` variants.
3. Asserts `identify_file_version` returns `"2.2.0"`.
4. Runs `mrd-upgrade` in both output-file and `--in-place` modes.
5. Runs `verify_upgrade.py`, which reads the result with the standard `BinaryMrdReader` and
   asserts item counts, data values, and that new optional fields are `None`.
6. Asserts that upgrading an already-current file raises `ValueError`.

`ReconData` and `ImageArray` are intentionally omitted from `generate_v220.py` because
writing them under the v2.2.0 codec hits a Yardl bug (structured-numpy-array fields
containing records with `Enum` fields raise `AttributeError` on `EnumSerializer.write` —
see <https://github.com/microsoft/yardl/issues/284>). `verify_upgrade.py` asserts their
counts are `0` accordingly, so the v2.2.0 code paths for those two variants are exercised
for structural correctness only (via `_V220ReconBufferSerializer` and friends being
constructed and registered in `_build_v220_stream_item_union()`) but not round-tripped
end-to-end.

## Extending for future versions

To add support for a future upgrade path (e.g. v2.2.1 → v2.2.2):

1. Register the v2.2.1 schema in `_schema_registry.py` (add a frozen `_V221_SCHEMA`
   literal copied from `MrdReaderBase.schema` *before* bumping the library, and add an
   entry to `_PAST_SCHEMAS`).
2. Write layout serializers in a new `_v221_reader.py` exposing a `V221MrdReader`.
3. In `__init__.py`, add `"2.2.1": "2.2.2"` to `_SUPPORTED_UPGRADES` **and** add the
   corresponding `_upgrade_221_to_222` function to `_UPGRADE_FUNCTIONS`. Multi-step
   chaining (e.g. v2.2.0 → v2.2.2) is handled automatically by `upgrade_mrd_file`.
4. Extract the `python/mrd/` tree from the v2.2.1 git tag via `git archive` in
   `test-upgrade.sh` and add a v2.2.1 generator/verifier pair.

The version-detection and dispatch pipeline requires no other changes.
