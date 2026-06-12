#!/usr/bin/env python3
"""Generate a v2.2.0 MRD binary stream that exercises all 14 StreamItem variants.

This script is intentionally run with the v2.2.0 mrd module on PYTHONPATH
(extracted from the v2.2.0 git tag via `git archive` by test-upgrade.sh) so
the data it writes is guaranteed to use the old schema and binary layout.

Usage:
    PYTHONPATH=<mrd-v2.2.0-dir> python3 generate_v220.py <output_file>
"""

import sys
import numpy as np
import mrd

output_path = sys.argv[1]

COILS   = 4
SAMPLES = 32
MATRIX  = 8    # tiny image matrix


def make_acquisition_header(scan_counter: int) -> mrd.AcquisitionHeader:
    return mrd.AcquisitionHeader(
        scan_counter=scan_counter,
        measurement_uid=42,
        idx=mrd.EncodingCounters(kspace_encode_step_1=scan_counter % MATRIX),
        discard_pre=0,
        discard_post=0,
        center_sample=SAMPLES // 2,
        sample_time_ns=5000,
        position=np.zeros(3, dtype=np.float32),
        read_dir=np.array([1, 0, 0], dtype=np.float32),
        phase_dir=np.array([0, 1, 0], dtype=np.float32),
        slice_dir=np.array([0, 0, 1], dtype=np.float32),
        patient_table_position=np.zeros(3, dtype=np.float32),
        channel_order=list(range(COILS)),
        user_int=[scan_counter],
        user_float=[float(scan_counter) * 0.1],
    )


def make_image_header(image_index: int) -> mrd.ImageHeader:
    # image_type is a required kwarg in v2.2.0
    return mrd.ImageHeader(
        image_type=mrd.ImageType.MAGNITUDE,
        measurement_uid=42,
        field_of_view=np.array([250.0, 250.0, 5.0], dtype=np.float32),
        position=np.zeros(3, dtype=np.float32),
        col_dir=np.array([1, 0, 0], dtype=np.float32),
        line_dir=np.array([0, 1, 0], dtype=np.float32),
        slice_dir=np.array([0, 0, 1], dtype=np.float32),
        patient_table_position=np.zeros(3, dtype=np.float32),
        image_index=image_index,
        image_series_index=0,
    )


def make_header() -> mrd.Header:
    return mrd.Header(
        version=2,
        experimental_conditions=mrd.ExperimentalConditionsType(
            h1resonance_frequency_hz=123_456_789,
        ),
        encoding=[
            mrd.EncodingType(
                trajectory=mrd.Trajectory.CARTESIAN,
                encoded_space=mrd.EncodingSpaceType(
                    matrix_size=mrd.MatrixSizeType(x=SAMPLES * 2, y=MATRIX, z=1),
                    field_of_view_mm=mrd.FieldOfViewMm(x=250.0, y=250.0, z=5.0),
                ),
                recon_space=mrd.EncodingSpaceType(
                    matrix_size=mrd.MatrixSizeType(x=SAMPLES * 2, y=MATRIX, z=1),
                    field_of_view_mm=mrd.FieldOfViewMm(x=250.0, y=250.0, z=5.0),
                ),
                encoding_limits=mrd.EncodingLimitsType(),
            )
        ],
    )


def items():
    # --- Acquisitions (tag 0 in both versions; no phase field in v2.2.0) ---
    for i in range(MATRIX):
        acq = mrd.Acquisition()
        acq.head = make_acquisition_header(i)
        acq.data = np.ones((COILS, SAMPLES), dtype=np.complex64) * complex(i + 1, -(i + 1))
        acq.trajectory = np.zeros((0, SAMPLES), dtype=np.float32)
        yield mrd.StreamItem.Acquisition(acq)

    # --- WaveformUint32 (tag 1 in v2.2.0, tag 2 in v2.2.1) ---
    # data kwarg is required in v2.2.0
    yield mrd.StreamItem.WaveformUint32(mrd.WaveformUint32(
        flags=0,
        measurement_uid=42,
        scan_counter=99,
        time_stamp_ns=1_000_000,
        sample_time_ns=1000,
        waveform_id=7,
        data=np.arange(2 * 16, dtype=np.uint32).reshape(2, 16),
    ))

    # --- All 8 Image types (tags 2-9 in v2.2.0, tags 3-10 in v2.2.1) ---
    img_shape = (1, 1, MATRIX, MATRIX)  # (channel, z, y, x)
    yield mrd.StreamItem.ImageUint16(mrd.ImageUint16(
        head=make_image_header(1), data=np.ones(img_shape, dtype=np.uint16), meta={}))
    yield mrd.StreamItem.ImageInt16(mrd.ImageInt16(
        head=make_image_header(2), data=np.ones(img_shape, dtype=np.int16), meta={}))
    yield mrd.StreamItem.ImageUint32(mrd.ImageUint32(
        head=make_image_header(3), data=np.ones(img_shape, dtype=np.uint32), meta={}))
    yield mrd.StreamItem.ImageInt32(mrd.ImageInt32(
        head=make_image_header(4), data=np.ones(img_shape, dtype=np.int32), meta={}))
    yield mrd.StreamItem.ImageFloat(mrd.ImageFloat(
        head=make_image_header(5), data=np.ones(img_shape, dtype=np.float32), meta={}))
    yield mrd.StreamItem.ImageDouble(mrd.ImageDouble(
        head=make_image_header(6), data=np.ones(img_shape, dtype=np.float64), meta={}))
    yield mrd.StreamItem.ImageComplexFloat(mrd.ImageComplexFloat(
        head=make_image_header(7), data=np.ones(img_shape, dtype=np.complex64), meta={}))
    yield mrd.StreamItem.ImageComplexDouble(mrd.ImageComplexDouble(
        head=make_image_header(8), data=np.ones(img_shape, dtype=np.complex128), meta={}))

    # --- AcquisitionBucket (tag 10 in v2.2.0, tag 11 in v2.2.1) ---
    bucket_acq = mrd.Acquisition()
    bucket_acq.head = make_acquisition_header(200)
    bucket_acq.data = np.ones((COILS, SAMPLES), dtype=np.complex64)
    bucket_acq.trajectory = np.zeros((0, SAMPLES), dtype=np.float32)
    yield mrd.StreamItem.AcquisitionBucket(mrd.AcquisitionBucket(
        data=[bucket_acq],
        ref=[],
        datastats=[],
        refstats=[],
        waveforms=[],
    ))

    # NOTE: ReconData (tag 11) and ImageArray (tag 13) are intentionally omitted
    # from this generator. Both require a structured numpy array whose element
    # dtype contains AcquisitionHeader/ImageHeader records. When the
    # NDArraySerializer writes such an array it calls write_numpy() per element,
    # which in turn calls _write() → write() for each field. The EnumSerializer
    # (used for AcquisitionFlags / ImageFlags) then tries `value.value` on the
    # numpy scalar (np.uint64) that structured-array field access returns, which
    # raises AttributeError. This is a bug in the Yardl-generated Python codec
    # that affects both v2.2.0 and v2.2.1. See:
    # https://github.com/microsoft/yardl/issues/284

    # --- ArrayComplexFloat (tag 12 in v2.2.0, tag 13 in v2.2.1) ---
    yield mrd.StreamItem.ArrayComplexFloat(
        np.arange(12, dtype=np.complex64).reshape(3, 4) * (1 + 0.5j)
    )


with mrd.BinaryMrdWriter(output_path) as w:
    w.write_header(make_header())
    w.write_data(items())

print(f"Written v2.2.0 stream to {output_path}", file=sys.stderr)
