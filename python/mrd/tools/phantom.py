import sys
import argparse
import numpy as np

from typing import Generator

import mrd
from mrd.tools import simulation
from mrd.tools.transform import image_to_kspace


def generate(output_file, matrix, coils, oversampling, repetitions, noise_level):
    output = sys.stdout.buffer
    if output_file is not None:
        output = output_file

    nx = matrix
    ny = matrix
    nkx = oversampling * nx
    nky = ny
    fov = 300
    slice_thickness = 5

    h = mrd.Header()

    s = mrd.SubjectInformationType()
    s.patient_id = "1234BGVF"
    s.patient_name = "John Doe"
    h.subject_information = s

    exp = mrd.ExperimentalConditionsType()
    exp.h1resonance_frequency_hz = 128000000
    h.experimental_conditions = exp

    sys_info = mrd.AcquisitionSystemInformationType()
    sys_info.receiver_channels = coils
    h.acquisition_system_information = sys_info

    e = mrd.EncodingSpaceType()
    e.matrix_size = mrd.MatrixSizeType(x=nkx, y=nky, z=1)
    e.field_of_view_mm = mrd.FieldOfViewMm(x=oversampling*fov, y=fov, z=slice_thickness)

    r = mrd.EncodingSpaceType()
    r.matrix_size = mrd.MatrixSizeType(x=nx, y=ny, z=1)
    r.field_of_view_mm = mrd.FieldOfViewMm(x=fov, y=fov, z=slice_thickness)

    limits1 = mrd.LimitType()
    limits1.minimum = 0
    limits1.center = round(ny / 2)
    limits1.maximum = ny - 1

    limits_rep = mrd.LimitType()
    limits_rep.minimum = 0
    limits_rep.center = round(repetitions / 2)
    limits_rep.maximum = repetitions - 1

    limits = mrd.EncodingLimitsType()
    limits.kspace_encoding_step_1 = limits1
    limits.repetition = limits_rep

    enc = mrd.EncodingType()
    enc.trajectory = mrd.Trajectory.CARTESIAN
    enc.encoded_space = e
    enc.recon_space = r
    enc.encoding_limits = limits
    h.encoding.append(enc)

    phantom = generate_coil_kspace(matrix, coils, oversampling)

    def generate_data() -> Generator[mrd.StreamItem, None, None]:
        # We'll reuse this Acquisition object
        acq = mrd.Acquisition()

        acq.data.resize((coils, nkx))
        acq.head.channel_order = list(range(coils))
        acq.head.center_sample = round(nkx / 2)
        acq.head.read_dir[0] = 1.0
        acq.head.phase_dir[1] = 1.0
        acq.head.slice_dir[2] = 1.0

        scan_counter = 0

        # Write out a few noise scans
        for n in range(32):
            noise = generate_noise((coils, nkx), noise_level)
            # Here's where we would make the noise correlated
            acq.head.scan_counter = scan_counter
            scan_counter += 1
            acq.head.flags = mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT
            acq.data[:] = noise
            yield mrd.StreamItem.Acquisition(acq)

        # Loop over the repetitions, add noise and serialize
        # Simulating a T-SENSE type scan
        for r in range(repetitions):
            noise = generate_noise(phantom.shape, noise_level)
            # Here's where we would make the noise correlated
            kspace = phantom + noise

            for line in range(nky):
                acq.head.scan_counter = scan_counter
                scan_counter += 1

                acq.head.flags = mrd.AcquisitionFlags(0)
                if line == 0:
                    acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_ENCODE_STEP_1
                    acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_SLICE
                    acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_REPETITION
                if line == nky - 1:
                    acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_ENCODE_STEP_1
                    acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_SLICE
                    acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_REPETITION

                acq.head.idx.kspace_encode_step_1 = line
                acq.head.idx.kspace_encode_step_2 = 0
                acq.head.idx.slice = 0
                acq.head.idx.repetition = r
                acq.data[:] = kspace[:, 0, line, :]
                yield mrd.StreamItem.Acquisition(acq)

    with mrd.BinaryMrdWriter(output) as w:
        w.write_header(h)
        w.write_data(generate_data())


def generate_noise(shape, noise_sigma, mean=0.0):
    rng = np.random.default_rng()
    noise = rng.normal(mean, noise_sigma, shape) + 1j * rng.normal(mean, noise_sigma, shape)
    return noise.astype(np.complex64)

def generate_coil_kspace(matrix_size, ncoils, oversampling):
    phan = simulation.generate_shepp_logan_phantom(matrix_size)
    coils = simulation.generate_birdcage_sensitivities(matrix_size, ncoils, 1.5)
    coils = phan * coils
    if oversampling > 1:
        c = (0,0)
        padding = round((oversampling * matrix_size - matrix_size) / 2)
        coils = np.pad(coils, (c, c, c, (padding,padding)), mode='constant')
    coils = image_to_kspace(coils, dim=(-1, -2)).astype(np.complex64)
    return coils


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates a phantom dataset in MRD format")
    parser.add_argument('-o', '--output', type=str, required=False, help="Output file, defaults to stdout")
    parser.add_argument('-m', '--matrix', type=int, required=False, help="Matrix size")
    parser.add_argument('-c', '--coils', type=int, required=False, help="Number of coils")
    parser.add_argument('-s', '--oversampling', type=int, required=False, help="Oversampling")
    parser.add_argument('-r', '--repetitions', type=int, required=False, help="Number of repetitions")
    # parser.add_argument('-a', '--acceleration', type=int, required=False, help="Acceleration", default=1)
    parser.add_argument('-n', '--noise-level', type=float, required=False, help="Noise level")
    parser.set_defaults(
        output=None,
        coils=8,
        matrix=256,
        oversampling=2,
        repetitions=1,
        noise_level=0.05
    )
    args = parser.parse_args()
    generate(args.output, args.matrix, args.coils, args.oversampling, args.repetitions, args.noise_level)
