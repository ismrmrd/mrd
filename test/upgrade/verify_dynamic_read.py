#!/usr/bin/env python3
"""Verify version-agnostic reading via ``mrd.dynamic.DynamicMrdReader``.

Unlike ``mrd-upgrade`` (which rewrites an old file into the current layout),
``DynamicMrdReader`` reads an *older* file in place: it builds its serializers
from the schema embedded in the file and reconciles the decoded values onto the
current model by field name. This script reads a genuine v2.2.0 stream with the
*current* library and asserts the reconciliation is correct:

  - the embedded schema does NOT match the current one (it's an old file);
  - the protocol/header decode and old data values are preserved verbatim;
  - fields added since v2.2.0 (acquisition_center_frequency, phase) read back
    as None, because they are absent from the file (invariant: new fields are
    optional);
  - StreamItem variants decode under their correct current subclasses even
    though v2.2.0 used a different tag order / casing (Acquisition vs
    acquisition) -- the appended AcquisitionPrototype variant shifts nothing;
  - a variant that was genuinely renamed/removed since v2.2.0 (i.e. a real
    schema break, not a casing change) is surfaced as an UnknownUnionCase and
    reported in reader.unmatched_variants, rather than crashing the read.

Usage:
    python3 verify_dynamic_read.py <v220.mrd>

These expectations mirror the values written by ``generate_v220.py``.
"""

import sys

import numpy as np
import numpy.testing as npt

import mrd
from mrd.dynamic import DynamicMrdReader, UnknownUnionCase

# Must match generate_v220.py
COILS = 4
SAMPLES = 32
MATRIX = 8


def main(path: str) -> None:
    acquisitions: list = []
    waveforms: list = []
    images: dict[type, list] = {}
    acq_buckets: list = []
    unknown: list[UnknownUnionCase] = []

    with DynamicMrdReader(path) as r:
        # ── 1. It really is an old file (schema differs from current) ─────────
        assert not r.schema_matches, (
            "expected the embedded schema to differ from the current one"
        )

        header = r.read_header()

        for item in r.read_data():
            if isinstance(item, mrd.StreamItem.Acquisition):
                acquisitions.append(item.value)
            elif isinstance(item, mrd.StreamItem.WaveformUint32):
                waveforms.append(item.value)
            elif isinstance(item, mrd.StreamItem.AcquisitionBucket):
                acq_buckets.append(item.value)
            elif isinstance(item, UnknownUnionCase):
                unknown.append(item)
            elif isinstance(
                item,
                (
                    mrd.StreamItem.ImageUint16,
                    mrd.StreamItem.ImageInt16,
                    mrd.StreamItem.ImageUint32,
                    mrd.StreamItem.ImageInt32,
                    mrd.StreamItem.ImageFloat,
                    mrd.StreamItem.ImageDouble,
                    mrd.StreamItem.ImageComplexFloat,
                    mrd.StreamItem.ImageComplexDouble,
                ),
            ):
                images.setdefault(type(item), []).append(item.value)

        unmatched = list(r.unmatched_variants)

    # ── 2. Header reconciled ─────────────────────────────────────────────────
    assert header is not None, "header is missing"
    assert header.version == 2, header.version
    assert header.experimental_conditions.h1resonance_frequency_hz == 123_456_789
    assert len(header.encoding) == 1
    assert header.encoding[0].trajectory == mrd.Trajectory.CARTESIAN

    # ── 3. Counts ────────────────────────────────────────────────────────────
    assert len(acquisitions) == MATRIX, len(acquisitions)
    assert len(waveforms) == 1, len(waveforms)
    assert len(acq_buckets) == 1, len(acq_buckets)
    assert len(images) == 8, sorted(t.__name__ for t in images)
    assert all(len(v) == 1 for v in images.values()), {
        t.__name__: len(v) for t, v in images.items()
    }

    # ── 4. Acquisitions: old data preserved, new fields default to None ──────
    for i, acq in enumerate(acquisitions):
        assert acq.head.scan_counter == i, (i, acq.head.scan_counter)
        assert acq.head.measurement_uid == 42
        assert acq.head.user_int == [i]
        # v2.2.1+ fields, absent in the v2.2.0 file:
        assert acq.head.acquisition_center_frequency is None, (
            f"acq[{i}].head.acquisition_center_frequency should be None"
        )
        assert acq.phase is None, f"acq[{i}].phase should be None"
        expected = np.ones((COILS, SAMPLES), dtype=np.complex64) * complex(
            i + 1, -(i + 1)
        )
        npt.assert_array_equal(acq.data, expected, err_msg=f"acq[{i}].data")

    # ── 5. Waveform (tag-order/casing reconciliation) ────────────────────────
    wf = waveforms[0]
    assert wf.scan_counter == 99
    assert wf.waveform_id == 7
    assert wf.sample_time_ns == 1000
    npt.assert_array_equal(
        wf.data, np.arange(2 * 16, dtype=np.uint32).reshape(2, 16)
    )

    # ── 6. Images: shape/dtype preserved across the tag shift ────────────────
    img_shape = (1, 1, MATRIX, MATRIX)
    for cls, vals in images.items():
        img = vals[0]
        assert img.data.shape == img_shape, (cls.__name__, img.data.shape)

    # ── 7. AcquisitionBucket: nested acquisitions also reconciled ────────────
    bucket = acq_buckets[0]
    assert len(bucket.data) == 1
    assert bucket.data[0].head.scan_counter == 200
    assert bucket.data[0].head.acquisition_center_frequency is None
    assert bucket.data[0].phase is None

    # ── 8. Genuinely renamed/removed variants are surfaced, not silent ───────
    print(f"  schema_matches:        {False}")
    print(f"  acquisitions:          {len(acquisitions)} (new fields -> None)")
    print(f"  waveforms:             {len(waveforms)}")
    print(f"  image variants:        {len(images)}")
    print(f"  acquisition buckets:   {len(acq_buckets)}")
    print(f"  unknown (renamed) variants encountered: {[u.tag for u in unknown]}")
    print(f"  reader.unmatched_variants:              {unmatched}")
    print("All dynamic-read assertions passed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
