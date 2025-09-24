import sys
import argparse
import numpy as np

from typing import Generator

import mrd
from mrd.tools import simulation
from mrd.tools.transform import image_to_kspace


def main():
    parser = argparse.ArgumentParser(description="Generates a phantom dataset in MRD format")
    parser.add_argument('-o', '--output', type=str, help="Output file, defaults to stdout")
    parser.add_argument('-c', '--coils', type=int, help="Number of coils")
    parser.add_argument('-m', '--matrix', type=int, help="Matrix size")
    parser.add_argument('-r', '--repetitions', type=int, help="Number of repetitions")
    parser.add_argument('-a', '--acceleration', type=int, help="Acceleration", default=1)
    parser.add_argument('-s', '--oversampling', type=int, help="Oversampling")
    parser.add_argument('-n', '--noise-level', type=float, help="Noise level")
    parser.add_argument('-w', '--calibration-width', type=int, help="Calibration width")
    parser.add_argument('-C', '--noise-calibration', action='store_true', help="Add noise calibration scans")
    parser.add_argument('-K', '--store-coordinates', action='store_true', help="Add k-space trajectory coordinates")
    parser.add_argument('--output-phantom', type=str, help="Write raw phantom array to file")
    parser.add_argument('--output-csm', type=str, help="Write coil sensitivities array to file")
    parser.add_argument('--output-coils', type=str, help="Write coil image array to file")
    parser.set_defaults(
        output=None,
        coils=8,
        matrix=256,
        repetitions=1,
        acceleration=1,
        oversampling=2,
        noise_level=0.05,
        calibration_width=0
    )
    args = parser.parse_args()

    output = sys.stdout.buffer
    if args.output is not None:
        output = args.output

    ncoils = args.coils
    nx = args.matrix
    ny = args.matrix
    nkx = args.oversampling * nx
    nky = ny
    fov = 300
    slice_thickness = 5

    h = mrd.Header()

    s = mrd.SubjectInformationType()
    s.patient_id = "1234BGVF"
    s.patient_name = "John Doe"
    h.subject_information = s

    meas = mrd.MeasurementInformationType()
    meas.patient_position = mrd.PatientPosition.H_FS
    h.measurement_information = meas

    sys_info = mrd.AcquisitionSystemInformationType()
    sys_info.receiver_channels = ncoils
    h.acquisition_system_information = sys_info

    exp = mrd.ExperimentalConditionsType()
    exp.h1resonance_frequency_hz = 128000000
    h.experimental_conditions = exp

    e = mrd.EncodingSpaceType()
    e.matrix_size = mrd.MatrixSizeType(x=nkx, y=nky, z=1)
    e.field_of_view_mm = mrd.FieldOfViewMm(x=args.oversampling*fov, y=fov, z=slice_thickness)

    r = mrd.EncodingSpaceType()
    r.matrix_size = mrd.MatrixSizeType(x=nx, y=ny, z=1)
    r.field_of_view_mm = mrd.FieldOfViewMm(x=fov, y=fov, z=slice_thickness)

    limits1 = mrd.LimitType()
    limits1.minimum = 0
    limits1.center = round(ny / 2)
    limits1.maximum = ny - 1

    limits_rep = mrd.LimitType()
    limits_rep.minimum = 0
    limits_rep.center = round(args.repetitions / 2)
    limits_rep.maximum = args.repetitions - 1

    limits = mrd.EncodingLimitsType()
    limits.kspace_encoding_step_1 = limits1
    limits.repetition = limits_rep

    enc = mrd.EncodingType()
    enc.trajectory = mrd.Trajectory.CARTESIAN
    enc.encoded_space = e
    enc.recon_space = r
    enc.encoding_limits = limits
    h.encoding.append(enc)

    phan = simulation.generate_shepp_logan_phantom(ny)
    if args.output_phantom is not None:
        with mrd.BinaryMrdWriter(args.output_phantom) as w:
            w.write_header(h)
            w.write_data([mrd.StreamItem.ArrayComplexFloat(phan)])

    csm = simulation.generate_birdcage_sensitivities(ny, ncoils, 1.5)
    if args.output_csm is not None:
        with mrd.BinaryMrdWriter(args.output_csm) as w:
            w.write_header(h)
            w.write_data([mrd.StreamItem.ArrayComplexFloat(csm)])

    coil_images = phan * csm
    if args.oversampling > 1:
        c = (0,0)
        padding = round((args.oversampling * nx - nx) / 2)
        coil_images = np.pad(coil_images, (c, c, c, (padding,padding)), mode='constant')

    if args.output_coils is not None:
        with mrd.BinaryMrdWriter(args.output_coils) as w:
            w.write_header(h)
            w.write_data([mrd.StreamItem.ArrayComplexFloat(coil_images)])

    coil_images = image_to_kspace(coil_images, dim=(-1, -2)).astype(np.complex64)

    def generate_data() -> Generator[mrd.StreamItem, None, None]:
        # We'll reuse this Acquisition object
        acq = mrd.Acquisition()

        acq.data.resize((ncoils, nkx))
        acq.head.channel_order = list(range(ncoils))
        acq.head.center_sample = round(nkx / 2)
        acq.head.read_dir[0] = 1.0
        acq.head.phase_dir[1] = 1.0
        acq.head.slice_dir[2] = 1.0

        scan_counter = 0

        if args.noise_calibration:
            # Write out a few noise scans
            for n in range(32):
                noise = generate_noise((ncoils, nkx), args.noise_level)
                # Here's where we would make the noise correlated
                acq.head.scan_counter = scan_counter
                scan_counter += 1
                acq.head.flags = mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT
                acq.data[:] = noise
                yield mrd.StreamItem.Acquisition(acq)

        calib_radius = args.calibration_width // 2
        calib_start = nky // 2 - calib_radius
        calib_end = nky // 2 + calib_radius - 1

        # Loop over the repetitions, add noise and serialize
        # Simulating a T-SENSE type scan
        for r in range(args.repetitions):
            for a in range(args.acceleration):
                noise = generate_noise(coil_images.shape, args.noise_level)
                # Here's where we would make the noise correlated
                kspace = coil_images + noise

                # TODO: This follows how we handle acceleration factor in ismrmrd:generate_cartesian_shepp_logan.cpp,
                #   however, it is NOT the same as the implementation in ismrmrd-python-tools:generate_cartesian_shepp_logan_dataset.py
                for line in range(nky):
                    is_calib_readout = ((line - a) % args.acceleration) != 0
                    in_calib_region = (line >= calib_start) and (line <= calib_end)
                    if is_calib_readout and not in_calib_region:
                        # Skip this line
                        continue

                    acq.head.flags = mrd.AcquisitionFlags(0)
                    acq.head.scan_counter = scan_counter
                    scan_counter += 1

                    if line == a:
                        acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_ENCODE_STEP_1
                        acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_SLICE
                        acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_REPETITION
                    elif line >= nky - args.acceleration:
                        acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_ENCODE_STEP_1
                        acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_SLICE
                        acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_REPETITION
                    elif in_calib_region:
                        if is_calib_readout:
                            acq.head.flags |= mrd.AcquisitionFlags.IS_PARALLEL_CALIBRATION
                        else:
                            acq.head.flags |= mrd.AcquisitionFlags.IS_PARALLEL_CALIBRATION_AND_IMAGING

                    acq.head.idx.kspace_encode_step_1 = line
                    acq.head.idx.slice = 0
                    acq.head.idx.repetition = r * args.acceleration + a
                    acq.data[:] = kspace[:, 0, line, :]

                    if args.store_coordinates:
                        acq.trajectory.resize((2, nkx))
                        ky = (line - (nky / 2)) / nky
                        for x in range(nkx):
                            kx = (x - (nkx / 2)) / nkx
                            acq.trajectory[0, x] = kx
                            acq.trajectory[1, x] = ky

                    yield mrd.StreamItem.Acquisition(acq)

    with mrd.BinaryMrdWriter(output) as w:
        w.write_header(h)
        w.write_data(generate_data())


def generate_noise(shape, noise_sigma, mean=0.0):
    rng = np.random.default_rng()
    noise = rng.normal(mean, noise_sigma, shape) + 1j * rng.normal(mean, noise_sigma, shape)
    return noise.astype(np.complex64)


if __name__ == "__main__":
    main()
