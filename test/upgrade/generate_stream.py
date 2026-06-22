#!/usr/bin/env python3
"""Generate a deterministic MRD stream using whichever `mrd` is on PYTHONPATH.

Run under different branches' generated `mrd` packages (via PYTHONPATH) to
produce files with different embedded schemas but identical logical content.
``verify_dynamic_stream.py`` then reads them back with the current library's
DynamicMrdReader and asserts the content survives the schema difference.

Only types/fields common to the relevant versions are used, so the same script
runs unchanged under each branch.

Usage:
    python3 generate_stream.py <output.mrd>
"""

import sys

import numpy as np

import mrd

COILS = 4
SAMPLES = 32
N_ACQ = 5


def acquisitions():
    for i in range(N_ACQ):
        head = mrd.AcquisitionHeader(
            flags=mrd.AcquisitionFlags.FIRST_IN_SLICE,
            idx=mrd.EncodingCounters(kspace_encode_step_1=i, slice=0),
            measurement_uid=42,
            scan_counter=i,
            user_int=[i],
        )
        data = np.ones((COILS, SAMPLES), dtype=np.complex64) * complex(i + 1, -(i + 1))
        traj = np.zeros((0, 0), dtype=np.float32)
        yield mrd.StreamItem.Acquisition(
            mrd.Acquisition(head=head, data=data, trajectory=traj)
        )


def waveform():
    return mrd.StreamItem.WaveformUint32(
        mrd.Waveform(
            flags=0,
            measurement_uid=1,
            scan_counter=99,
            time_stamp_ns=0,
            sample_time_ns=1000,
            waveform_id=7,
            data=np.arange(2 * 16, dtype=np.uint32).reshape(2, 16),
        )
    )


def items():
    # Note: images are intentionally omitted from this portable generator
    # because ImageData rank differs across branches (main is 4-D, this branch
    # is 5-D), which the *writer* enforces. Image reconciliation on read is
    # covered by the v2.2.0 case (verify_dynamic_read.py). Acquisitions and the
    # waveform exercise record reconciliation, nested records, NDArrays and
    # union tag handling, and use only branch-stable types.
    yield from acquisitions()
    yield waveform()


def main(path: str) -> None:
    header = mrd.Header(
        version=2,
        subject_information=mrd.SubjectInformationType(patient_name="John Doe"),
        experimental_conditions=mrd.ExperimentalConditionsType(
            h1resonance_frequency_hz=123_456_789
        ),
    )
    with mrd.BinaryMrdWriter(path) as w:
        w.write_header(header)
        w.write_data(items())
    print(f"Wrote stream to {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
