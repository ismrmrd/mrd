"""Custom serializers and reader for MRD v2.2.0 binary files.

This module provides backward-compatible deserialization for MRD files written
with schema version 2.2.0, producing v2.2.1 objects ready for re-serialization.

Changes from v2.2.0 → v2.2.1:
  - AcquisitionHeader: added `acquisitionCenterFrequency: uint64?` at field index 4
  - Acquisition: added `phase: AcquisitionPhase?` at field index 2
  - StreamItem: inserted AcquisitionPrototype at tag index 1, shifting all
    subsequent variant tag indices by +1
"""

import collections.abc
import typing

import mrd
from mrd import _binary
from mrd.binary import (
    AcquisitionFlags,
    EncodingCountersSerializer,
    HeaderSerializer,
    WaveformSerializer,
    ImageSerializer,
    ImageArraySerializer,
    SamplingDescriptionSerializer,
    EncodingLimitsTypeSerializer,
)
from mrd.types import (
    Acquisition,
    AcquisitionHeader,
    AcquisitionBucket,
    ReconBuffer,
    ReconAssembly,
    ReconData,
    StreamItem,
)


# ---------------------------------------------------------------------------
# v2.2.0 AcquisitionHeaderSerializer
# 19 fields (no acquisitionCenterFrequency)
# ---------------------------------------------------------------------------

class _V220AcquisitionHeaderSerializer(_binary.RecordSerializer[AcquisitionHeader]):
    """Reads a v2.2.0 AcquisitionHeader (19 fields) and returns a v2.2.1 object."""

    def __init__(self) -> None:
        super().__init__([
            ("flags",                   _binary.EnumSerializer(_binary.uint64_serializer, AcquisitionFlags)),
            ("idx",                     EncodingCountersSerializer()),
            ("measurement_uid",         _binary.uint32_serializer),
            ("scan_counter",            _binary.OptionalSerializer(_binary.uint32_serializer)),
            # NOTE: acquisitionCenterFrequency is absent in v2.2.0
            ("acquisition_time_stamp_ns",  _binary.OptionalSerializer(_binary.uint64_serializer)),
            ("physiology_time_stamp_ns",   _binary.VectorSerializer(_binary.uint64_serializer)),
            ("channel_order",           _binary.VectorSerializer(_binary.uint32_serializer)),
            ("discard_pre",             _binary.OptionalSerializer(_binary.uint32_serializer)),
            ("discard_post",            _binary.OptionalSerializer(_binary.uint32_serializer)),
            ("center_sample",           _binary.OptionalSerializer(_binary.uint32_serializer)),
            ("encoding_space_ref",      _binary.OptionalSerializer(_binary.uint32_serializer)),
            ("sample_time_ns",          _binary.OptionalSerializer(_binary.uint64_serializer)),
            ("position",                _binary.FixedNDArraySerializer(_binary.float32_serializer, (3,))),
            ("read_dir",                _binary.FixedNDArraySerializer(_binary.float32_serializer, (3,))),
            ("phase_dir",               _binary.FixedNDArraySerializer(_binary.float32_serializer, (3,))),
            ("slice_dir",               _binary.FixedNDArraySerializer(_binary.float32_serializer, (3,))),
            ("patient_table_position",  _binary.FixedNDArraySerializer(_binary.float32_serializer, (3,))),
            ("user_int",                _binary.VectorSerializer(_binary.int32_serializer)),
            ("user_float",              _binary.VectorSerializer(_binary.float32_serializer)),
        ])

    def write(self, stream: _binary.CodedOutputStream, value: AcquisitionHeader) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def write_numpy(self, stream: _binary.CodedOutputStream, value) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def read(self, stream: _binary.CodedInputStream) -> AcquisitionHeader:
        fv = self._read(stream)
        return AcquisitionHeader(
            flags=fv[0],
            idx=fv[1],
            measurement_uid=fv[2],
            scan_counter=fv[3],
            acquisition_center_frequency=None,  # not present in v2.2.0
            acquisition_time_stamp_ns=fv[4],
            physiology_time_stamp_ns=fv[5],
            channel_order=fv[6],
            discard_pre=fv[7],
            discard_post=fv[8],
            center_sample=fv[9],
            encoding_space_ref=fv[10],
            sample_time_ns=fv[11],
            position=fv[12],
            read_dir=fv[13],
            phase_dir=fv[14],
            slice_dir=fv[15],
            patient_table_position=fv[16],
            user_int=fv[17],
            user_float=fv[18],
        )


# ---------------------------------------------------------------------------
# v2.2.0 AcquisitionSerializer
# 3 fields: head, data, trajectory  (no phase)
# ---------------------------------------------------------------------------

class _V220AcquisitionSerializer(_binary.RecordSerializer[Acquisition]):
    """Reads a v2.2.0 Acquisition (3 fields) and returns a v2.2.1 object."""

    def __init__(self) -> None:
        super().__init__([
            ("head",       _V220AcquisitionHeaderSerializer()),
            ("data",       _binary.NDArraySerializer(_binary.complexfloat32_serializer, 2)),
            # NOTE: phase is absent in v2.2.0
            ("trajectory", _binary.NDArraySerializer(_binary.float32_serializer, 2)),
        ])

    def write(self, stream: _binary.CodedOutputStream, value: Acquisition) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def write_numpy(self, stream: _binary.CodedOutputStream, value) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def read(self, stream: _binary.CodedInputStream) -> Acquisition:
        fv = self._read(stream)
        return Acquisition(
            head=fv[0],
            data=fv[1],
            phase=None,        # not present in v2.2.0
            trajectory=fv[2],
        )


# ---------------------------------------------------------------------------
# v2.2.0 AcquisitionBucketSerializer
# Same fields as v2.2.1 but uses _V220AcquisitionSerializer internally
# ---------------------------------------------------------------------------

class _V220AcquisitionBucketSerializer(_binary.RecordSerializer[AcquisitionBucket]):
    def __init__(self) -> None:
        super().__init__([
            ("data",       _binary.VectorSerializer(_V220AcquisitionSerializer())),
            ("ref",        _binary.VectorSerializer(_V220AcquisitionSerializer())),
            ("datastats",  _binary.VectorSerializer(EncodingLimitsTypeSerializer())),
            ("refstats",   _binary.VectorSerializer(EncodingLimitsTypeSerializer())),
            ("waveforms",  _binary.VectorSerializer(WaveformSerializer(_binary.uint32_serializer))),
        ])

    def write(self, stream: _binary.CodedOutputStream, value: AcquisitionBucket) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def write_numpy(self, stream: _binary.CodedOutputStream, value) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def read(self, stream: _binary.CodedInputStream) -> AcquisitionBucket:
        fv = self._read(stream)
        return AcquisitionBucket(data=fv[0], ref=fv[1], datastats=fv[2], refstats=fv[3], waveforms=fv[4])


# ---------------------------------------------------------------------------
# v2.2.0 ReconBufferSerializer
# Same structure as v2.2.1 but AcquisitionHeader NDArray uses v2.2.0 header
# ---------------------------------------------------------------------------

class _V220ReconBufferSerializer(_binary.RecordSerializer[ReconBuffer]):
    def __init__(self) -> None:
        super().__init__([
            ("data",      _binary.NDArraySerializer(_binary.complexfloat32_serializer, 7)),
            ("trajectory", _binary.NDArraySerializer(_binary.float32_serializer, 7)),
            ("density",   _binary.OptionalSerializer(_binary.NDArraySerializer(_binary.float32_serializer, 6))),
            ("headers",   _binary.NDArraySerializer(_V220AcquisitionHeaderSerializer(), 5)),
            ("sampling",  SamplingDescriptionSerializer()),
        ])

    def write(self, stream: _binary.CodedOutputStream, value: ReconBuffer) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def write_numpy(self, stream: _binary.CodedOutputStream, value) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def read(self, stream: _binary.CodedInputStream) -> ReconBuffer:
        fv = self._read(stream)
        return ReconBuffer(data=fv[0], trajectory=fv[1], density=fv[2], headers=fv[3], sampling=fv[4])


class _V220ReconAssemblySerializer(_binary.RecordSerializer[ReconAssembly]):
    def __init__(self) -> None:
        super().__init__([
            ("data", _V220ReconBufferSerializer()),
            ("ref",  _binary.OptionalSerializer(_V220ReconBufferSerializer())),
        ])

    def write(self, stream: _binary.CodedOutputStream, value: ReconAssembly) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def write_numpy(self, stream: _binary.CodedOutputStream, value) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def read(self, stream: _binary.CodedInputStream) -> ReconAssembly:
        fv = self._read(stream)
        return ReconAssembly(data=fv[0], ref=fv[1])


class _V220ReconDataSerializer(_binary.RecordSerializer[ReconData]):
    def __init__(self) -> None:
        super().__init__([
            ("buffers", _binary.VectorSerializer(_V220ReconAssemblySerializer())),
        ])

    def write(self, stream: _binary.CodedOutputStream, value: ReconData) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def write_numpy(self, stream: _binary.CodedOutputStream, value) -> None:
        raise NotImplementedError("V220 serializers are read-only")

    def read(self, stream: _binary.CodedInputStream) -> ReconData:
        fv = self._read(stream)
        return ReconData(buffers=fv[0])


# ---------------------------------------------------------------------------
# v2.2.0 StreamItem UnionSerializer
#
# v2.2.0 had 14 variants; AcquisitionPrototype did not exist.
# Tag bytes 0–13 map to types in v2.2.0 order, but we output v2.2.1 objects
# (the StreamItem.* class indices are already correct for v2.2.1 output).
# ---------------------------------------------------------------------------

def _build_v220_stream_item_union() -> _binary.UnionSerializer:
    return _binary.UnionSerializer(StreamItem, [
        # tag 0 → Acquisition (v2.2.1 index=0, no change)
        (StreamItem.Acquisition,        _V220AcquisitionSerializer()),
        # tag 1 → WaveformUint32 (v2.2.1 index=2, was index=1 in v2.2.0)
        (StreamItem.WaveformUint32,     WaveformSerializer(_binary.uint32_serializer)),
        # tag 2-9 → Image types (v2.2.1 indices=3-10, were 2-9 in v2.2.0)
        (StreamItem.ImageUint16,        ImageSerializer(_binary.uint16_serializer)),
        (StreamItem.ImageInt16,         ImageSerializer(_binary.int16_serializer)),
        (StreamItem.ImageUint32,        ImageSerializer(_binary.uint32_serializer)),
        (StreamItem.ImageInt32,         ImageSerializer(_binary.int32_serializer)),
        (StreamItem.ImageFloat,         ImageSerializer(_binary.float32_serializer)),
        (StreamItem.ImageDouble,        ImageSerializer(_binary.float64_serializer)),
        (StreamItem.ImageComplexFloat,  ImageSerializer(_binary.complexfloat32_serializer)),
        (StreamItem.ImageComplexDouble, ImageSerializer(_binary.complexfloat64_serializer)),
        # tag 10 → AcquisitionBucket (v2.2.1 index=11, was index=10 in v2.2.0)
        (StreamItem.AcquisitionBucket,  _V220AcquisitionBucketSerializer()),
        # tag 11 → ReconData (v2.2.1 index=12, was index=11 in v2.2.0)
        (StreamItem.ReconData,          _V220ReconDataSerializer()),
        # tag 12 → ArrayComplexFloat (v2.2.1 index=13, was index=12 in v2.2.0)
        (StreamItem.ArrayComplexFloat,  _binary.DynamicNDArraySerializer(_binary.complexfloat32_serializer)),
        # tag 13 → ImageArray (v2.2.1 index=14, was index=13 in v2.2.0)
        (StreamItem.ImageArray,         ImageArraySerializer()),
    ])


# ---------------------------------------------------------------------------
# V220MrdReader: reads a v2.2.0 file, produces v2.2.1 objects
# ---------------------------------------------------------------------------

class V220MrdReader(_binary.BinaryProtocolReader):
    """Reads an MRD v2.2.0 binary file, yielding v2.2.1-compatible objects.

    Note: this class deliberately does *not* inherit from MrdReaderBase, so the
    protocol state machine (call-order enforcement, close-completeness check) is
    bypassed entirely.  It is only used internally by _upgrade_220_to_221, which
    calls read_header() exactly once followed by read_data() exactly once.
    """

    def __init__(self, stream: typing.Union[typing.BinaryIO, str]) -> None:
        # Pass None to skip schema validation — we deliberately accept v2.2.0.
        super().__init__(stream, expected_schema=None)
        self._stream_item_union = _build_v220_stream_item_union()

    def __enter__(self) -> "V220MrdReader":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._close()

    def read_header(self) -> typing.Optional[mrd.Header]:
        return _binary.OptionalSerializer(HeaderSerializer()).read(self._stream)

    def read_data(self) -> collections.abc.Iterable[StreamItem]:
        return _binary.StreamSerializer(self._stream_item_union).read(self._stream)
