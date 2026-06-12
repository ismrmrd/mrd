#!/usr/bin/env python3
"""Verify that an upgraded MRD file contains the expected data.

Reads the upgraded v2.2.1 file with the standard BinaryMrdReader and asserts:
  - All 14 original StreamItem types are present with the right counts
  - Tag indices were remapped correctly (WaveformUint32 and Image types are read
    back under their correct v2.2.1 StreamItem subclasses)
  - Key data values from generate_v220.py are preserved
  - New v2.2.1-only fields (acquisition_center_frequency, phase) are None

Usage:
    python3 verify_upgrade.py <upgraded_v221.mrd>
"""

import sys
import numpy as np
import numpy.testing as npt
import mrd
from mrd.tools.upgrade import identify_file_version

COILS   = 4
SAMPLES = 32
MATRIX  = 8

upgraded_path = sys.argv[1]

# ── 1. Schema version check ───────────────────────────────────────────────────
version = identify_file_version(upgraded_path)
assert version == "2.2.1", f"Expected schema version 2.2.1, got {version!r}"

# ── 2. Read all items ─────────────────────────────────────────────────────────
acquisitions       = []
waveforms          = []
images_uint16      = []
images_int16       = []
images_uint32      = []
images_int32       = []
images_float       = []
images_double      = []
images_cf          = []
images_cd          = []
acq_buckets        = []
recon_datas        = []  # not generated; see generate_v220.py comment
arrays_cf          = []
image_arrays       = []  # not generated; see generate_v220.py comment
unexpected         = []

with mrd.BinaryMrdReader(upgraded_path) as r:
    header = r.read_header()
    for item in r.read_data():
        match item:
            case mrd.StreamItem.Acquisition():          acquisitions.append(item.value)
            case mrd.StreamItem.WaveformUint32():       waveforms.append(item.value)
            case mrd.StreamItem.ImageUint16():          images_uint16.append(item.value)
            case mrd.StreamItem.ImageInt16():           images_int16.append(item.value)
            case mrd.StreamItem.ImageUint32():          images_uint32.append(item.value)
            case mrd.StreamItem.ImageInt32():           images_int32.append(item.value)
            case mrd.StreamItem.ImageFloat():           images_float.append(item.value)
            case mrd.StreamItem.ImageDouble():          images_double.append(item.value)
            case mrd.StreamItem.ImageComplexFloat():    images_cf.append(item.value)
            case mrd.StreamItem.ImageComplexDouble():   images_cd.append(item.value)
            case mrd.StreamItem.AcquisitionBucket():    acq_buckets.append(item.value)
            case mrd.StreamItem.ReconData():            recon_datas.append(item.value)
            case mrd.StreamItem.ArrayComplexFloat():    arrays_cf.append(item.value)
            case mrd.StreamItem.ImageArray():           image_arrays.append(item.value)
            case _:                                     unexpected.append(item)

# ── 3. Header ─────────────────────────────────────────────────────────────────
assert header is not None, "Header is missing"
assert header.version == 2
assert header.experimental_conditions.h1resonance_frequency_hz == 123_456_789
assert len(header.encoding) == 1
assert header.encoding[0].trajectory == mrd.Trajectory.CARTESIAN

# ── 4. Item counts ────────────────────────────────────────────────────────────
assert len(unexpected)   == 0,  f"Unexpected item types: {[type(x).__name__ for x in unexpected]}"
assert len(acquisitions) == MATRIX, f"Expected {MATRIX} acquisitions, got {len(acquisitions)}"
assert len(waveforms)    == 1,  f"Expected 1 waveform, got {len(waveforms)}"
assert len(images_uint16)== 1
assert len(images_int16) == 1
assert len(images_uint32)== 1
assert len(images_int32) == 1
assert len(images_float) == 1
assert len(images_double)== 1
assert len(images_cf)    == 1
assert len(images_cd)    == 1
assert len(acq_buckets)  == 1
assert len(recon_datas)  == 0,  "ReconData not generated; see generate_v220.py"
assert len(arrays_cf)    == 1
assert len(image_arrays) == 0,  "ImageArray not generated; see generate_v220.py"

# ── 5. Acquisitions: data values + new fields are None ───────────────────────
for i, acq in enumerate(acquisitions):
    assert acq.head.scan_counter == i,       f"acq[{i}].head.scan_counter mismatch"
    assert acq.head.measurement_uid == 42,   f"acq[{i}].head.measurement_uid mismatch"
    assert acq.head.user_int == [i],         f"acq[{i}].head.user_int mismatch"
    # New v2.2.1 fields must be None (absent in the v2.2.0 source)
    assert acq.head.acquisition_center_frequency is None, \
        f"acq[{i}].head.acquisition_center_frequency should be None"
    assert acq.phase is None, \
        f"acq[{i}].phase should be None"
    # Data values preserved
    expected_data = np.ones((COILS, SAMPLES), dtype=np.complex64) * complex(i + 1, -(i + 1))
    npt.assert_array_equal(acq.data, expected_data, err_msg=f"acq[{i}].data mismatch")

# ── 6. WaveformUint32 ─────────────────────────────────────────────────────────
wf = waveforms[0]
assert wf.scan_counter  == 99
assert wf.waveform_id   == 7
assert wf.sample_time_ns == 1000
npt.assert_array_equal(wf.data, np.arange(2 * 16, dtype=np.uint32).reshape(2, 16))

# ── 7. Image types: data shape + dtype + image_index ─────────────────────────
img_shape = (1, 1, MATRIX, MATRIX)
for idx, img in enumerate(images_uint16):
    assert img.head.image_index == 1
    assert img.data.shape == img_shape, f"images_uint16[{idx}].data.shape mismatch"
    assert img.data.dtype == np.uint16,  f"images_uint16[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_int16):
    assert img.head.image_index == 2
    assert img.data.shape == img_shape, f"images_int16[{idx}].data.shape mismatch"
    assert img.data.dtype == np.int16,   f"images_int16[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_uint32):
    assert img.head.image_index == 3
    assert img.data.shape == img_shape, f"images_uint32[{idx}].data.shape mismatch"
    assert img.data.dtype == np.uint32,  f"images_uint32[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_int32):
    assert img.head.image_index == 4
    assert img.data.shape == img_shape, f"images_int32[{idx}].data.shape mismatch"
    assert img.data.dtype == np.int32,   f"images_int32[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_float):
    assert img.head.image_index == 5
    assert img.data.shape == img_shape, f"images_float[{idx}].data.shape mismatch"
    assert img.data.dtype == np.float32, f"images_float[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_double):
    assert img.head.image_index == 6
    assert img.data.shape == img_shape, f"images_double[{idx}].data.shape mismatch"
    assert img.data.dtype == np.float64, f"images_double[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_cf):
    assert img.head.image_index == 7
    assert img.data.shape == img_shape,   f"images_cf[{idx}].data.shape mismatch"
    assert img.data.dtype == np.complex64, f"images_cf[{idx}].data.dtype mismatch"
for idx, img in enumerate(images_cd):
    assert img.head.image_index == 8
    assert img.data.shape == img_shape,    f"images_cd[{idx}].data.shape mismatch"
    assert img.data.dtype == np.complex128, f"images_cd[{idx}].data.dtype mismatch"

# ── 8. AcquisitionBucket ──────────────────────────────────────────────────────
bucket = acq_buckets[0]
assert len(bucket.data) == 1
assert bucket.data[0].head.scan_counter == 200
assert bucket.data[0].head.acquisition_center_frequency is None
assert bucket.data[0].phase is None

# ── 9. ReconData / ImageArray (omitted from generator — see generate_v220.py) ─
# (no assertions)

# ── 10. ArrayComplexFloat ─────────────────────────────────────────────────────
arr = arrays_cf[0]
assert arr.shape == (3, 4)
npt.assert_array_equal(arr, np.arange(12, dtype=np.complex64).reshape(3, 4) * (1 + 0.5j))

# ── 11. ImageArray (omitted) ─────────────────────────────────────────────────
# (no assertions)

print("All assertions passed.")
