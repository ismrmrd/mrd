#!/usr/bin/env python3
"""Read a stream written by generate_stream.py with the CURRENT library and
assert version-agnostic correctness via DynamicMrdReader.

Also reports whether the stock BinaryMrdReader accepts the file: it should be
rejected when the file's embedded schema differs from the current one (e.g. a
file written by another branch) and accepted when it matches.

Usage:
    python3 verify_dynamic_stream.py <stream.mrd>
"""

import sys

import numpy as np
import numpy.testing as npt

import mrd
from mrd.dynamic import DynamicMrdReader, UnknownUnionCase

COILS = 4
SAMPLES = 32
N_ACQ = 5


def binary_reader_status(path: str) -> str:
    try:
        with mrd.BinaryMrdReader(path) as r:
            r.read_header()
            for _ in r.read_data():
                pass
        return "accepted"
    except Exception as e:  # noqa: BLE001
        return f"rejected ({type(e).__name__})"


def main(path: str) -> None:
    acqs = []
    waveforms = []
    unknown = []

    with DynamicMrdReader(path) as r:
        matches = r.schema_matches
        header = r.read_header()
        for item in r.read_data():
            if isinstance(item, mrd.StreamItem.Acquisition):
                acqs.append(item.value)
            elif isinstance(item, mrd.StreamItem.WaveformUint32):
                waveforms.append(item.value)
            elif isinstance(item, UnknownUnionCase):
                unknown.append(item)
        unmatched = list(r.unmatched_variants)

    # Header
    assert header is not None
    assert header.version == 2, header.version
    assert header.subject_information.patient_name == "John Doe"
    assert header.experimental_conditions.h1resonance_frequency_hz == 123_456_789

    # Counts
    assert len(acqs) == N_ACQ, len(acqs)
    assert len(waveforms) == 1, len(waveforms)

    # Acquisition values
    for i, acq in enumerate(acqs):
        assert acq.head.scan_counter == i
        assert acq.head.measurement_uid == 42
        assert acq.head.user_int == [i]
        expected = np.ones((COILS, SAMPLES), dtype=np.complex64) * complex(
            i + 1, -(i + 1)
        )
        npt.assert_array_equal(acq.data, expected, err_msg=f"acq[{i}].data")

    # Waveform
    wf = waveforms[0]
    assert wf.scan_counter == 99 and wf.waveform_id == 7 and wf.sample_time_ns == 1000
    npt.assert_array_equal(wf.data, np.arange(2 * 16, dtype=np.uint32).reshape(2, 16))

    print(f"  schema_matches:     {matches}")
    print(f"  BinaryMrdReader:    {binary_reader_status(path)}")
    print(f"  DynamicMrdReader:   OK -> {len(acqs)} acq, {len(waveforms)} waveform")
    if unmatched:
        print(f"  unmatched variants (file-only): {unmatched}")
    print("  All stream assertions passed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
