import sys
import argparse
import numpy as np

from typing import Generator, Optional
from dataclasses import dataclass

import mrd
from mrd.tools import simulation
from mrd.tools.transform import image_to_kspace


@dataclass
class PhantomDefaults:
    """Default values for phantom generation parameters"""
    output: Optional[str] = None
    coils: int = 8
    matrix: int = 256
    repetitions: int = 1
    acceleration: int = 1
    oversampling: int = 2
    noise_level: float = 0.05
    calibration_width: int = 0
    noise_calibration: bool = False
    store_coordinates: bool = False
    output_phantom: Optional[str] = None
    output_csm: Optional[str] = None
    output_coils: Optional[str] = None


def generate_cartesian_phantom(output_file: Optional[str] = PhantomDefaults.output,
                               ncoils: int = PhantomDefaults.coils,
                               matrix_size: int = PhantomDefaults.matrix,
                               repetitions: int = PhantomDefaults.repetitions,
                               acceleration: int = PhantomDefaults.acceleration,
                               oversampling: int = PhantomDefaults.oversampling,
                               noise_level: float = PhantomDefaults.noise_level,
                               calibration_width: int = PhantomDefaults.calibration_width,
                               noise_calibration: bool = PhantomDefaults.noise_calibration,
                               store_coordinates: bool = PhantomDefaults.store_coordinates,
                               output_phantom: Optional[str] = PhantomDefaults.output_phantom,
                               output_csm: Optional[str] = PhantomDefaults.output_csm,
                               output_coils: Optional[str] = PhantomDefaults.output_coils):

    output = sys.stdout.buffer
    if output_file is not None:
        output = output_file

    nx = matrix_size
    ny = matrix_size
    nkx = oversampling * nx
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
    sys_info.coil_label = [mrd.CoilLabelType(coil_number=c, coil_name=f"Channel {c}") for c in range(ncoils)]
    h.acquisition_system_information = sys_info

    exp = mrd.ExperimentalConditionsType()
    exp.h1resonance_frequency_hz = 128000000
    h.experimental_conditions = exp

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

    if acceleration > 1:
        p = mrd.ParallelImagingType()
        p.acceleration_factor.kspace_encoding_step_1 = acceleration
        p.acceleration_factor.kspace_encoding_step_2 = 1
        p.calibration_mode = mrd.CalibrationMode.EMBEDDED
        enc.parallel_imaging = p

    h.encoding.append(enc)

    phan = simulation.generate_shepp_logan_phantom(ny)
    if output_phantom is not None:
        with mrd.BinaryMrdWriter(output_phantom) as w:
            w.write_header(h)
            w.write_data([mrd.StreamItem.ArrayComplexFloat(phan)])

    csm = simulation.generate_birdcage_sensitivities(ny, ncoils, 1.5)
    if output_csm is not None:
        with mrd.BinaryMrdWriter(output_csm) as w:
            w.write_header(h)
            w.write_data([mrd.StreamItem.ArrayComplexFloat(csm)])

    coil_images = phan * csm
    if oversampling > 1:
        c = (0,0)
        padding = round((oversampling * nx - nx) / 2)
        coil_images = np.pad(coil_images, (c, c, c, (padding,padding)), mode='constant')

    if output_coils is not None:
        with mrd.BinaryMrdWriter(output_coils) as w:
            w.write_header(h)
            w.write_data([mrd.StreamItem.ArrayComplexFloat(coil_images)])

    coil_images = image_to_kspace(coil_images, dim=(-1, -2)).astype(np.complex64)

    def generate_data() -> Generator[mrd.StreamItem, None, None]:

        def new_acquisition():
            """Create a new, default-initialized Acquisition object"""
            head = mrd.AcquisitionHeader()
            head.encoding_space_ref = 0
            head.sample_time_ns = 5000
            head.channel_order = list(range(ncoils))
            head.center_sample = round(nkx / 2)
            head.read_dir[0] = 1.0
            head.phase_dir[1] = 1.0
            head.slice_dir[2] = 1.0
            data = np.zeros((ncoils, nkx), dtype=np.complex64)
            return mrd.Acquisition(head=head, data=data)

        scan_counter = 0

        if noise_calibration:
            # Write out a few noise scans
            for n in range(32):
                acq = new_acquisition()
                noise = generate_noise(acq.data.shape, noise_level)
                # Here's where we would make the noise correlated
                acq.head.scan_counter = scan_counter
                scan_counter += 1
                acq.head.flags = mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT
                acq.data[:] = noise
                yield mrd.StreamItem.Acquisition(acq)

        calib_start = nky // 2 - calibration_width // 2

        # Loop over the repetitions, add noise and serialize
        # Simulating a T-SENSE type scan
        for r in range(repetitions):
            noise = generate_noise(coil_images.shape, noise_level)
            # Here's where we would make the noise correlated
            kspace = coil_images + noise

            a = r % acceleration
            for line in range(nky):
                is_sampled_line = ((line - a) % acceleration) == 0
                in_calib_region = (line >= calib_start) and (line < calib_start + calibration_width)
                if not is_sampled_line and not in_calib_region:
                    # Skip this line
                    continue

                acq = new_acquisition()
                acq.head.flags = mrd.AcquisitionFlags(0)
                acq.head.scan_counter = scan_counter
                scan_counter += 1

                if line == a:
                    acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_ENCODE_STEP_1
                    acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_SLICE
                    acq.head.flags |= mrd.AcquisitionFlags.FIRST_IN_REPETITION
                elif line >= nky - acceleration:
                    acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_ENCODE_STEP_1
                    acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_SLICE
                    acq.head.flags |= mrd.AcquisitionFlags.LAST_IN_REPETITION
                elif in_calib_region:
                    if not is_sampled_line:
                        acq.head.flags |= mrd.AcquisitionFlags.IS_PARALLEL_CALIBRATION
                    else:
                        acq.head.flags |= mrd.AcquisitionFlags.IS_PARALLEL_CALIBRATION_AND_IMAGING

                acq.head.idx.kspace_encode_step_1 = line
                acq.head.idx.slice = 0
                acq.head.idx.repetition = r
                acq.data[:] = kspace[:, 0, line, :]

                if store_coordinates:
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
    parser = argparse.ArgumentParser(description="Generates a phantom dataset in MRD format", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output', type=str, help="Output file, defaults to stdout")
    parser.add_argument('-c', '--coils', type=int, help=f"Number of coils")
    parser.add_argument('-m', '--matrix', type=int, help=f"Matrix size")
    parser.add_argument('-r', '--repetitions', type=int, help=f"Number of repetitions")
    parser.add_argument('-a', '--acceleration', type=int, help=f"Acceleration")
    parser.add_argument('-s', '--oversampling', type=int, help=f"Oversampling")
    parser.add_argument('-n', '--noise-level', type=float, help=f"Noise level")
    parser.add_argument('-w', '--calibration-width', type=int, help=f"Calibration width")
    parser.add_argument('-C', '--noise-calibration', action='store_true', help="Add noise calibration scans")
    parser.add_argument('-K', '--store-coordinates', action='store_true', help="Add k-space trajectory coordinates")
    parser.add_argument('--output-phantom', type=str, help="Write raw phantom array to file")
    parser.add_argument('--output-csm', type=str, help="Write coil sensitivities array to file")
    parser.add_argument('--output-coils', type=str, help="Write coil image array to file")

    # Use the defaults from our PhantomDefaults dataclass
    defaults = PhantomDefaults()
    parser.set_defaults(
        output=defaults.output,
        coils=defaults.coils,
        matrix=defaults.matrix,
        repetitions=defaults.repetitions,
        acceleration=defaults.acceleration,
        oversampling=defaults.oversampling,
        noise_level=defaults.noise_level,
        calibration_width=defaults.calibration_width,
        noise_calibration=defaults.noise_calibration,
        store_coordinates=defaults.store_coordinates,
        output_phantom=defaults.output_phantom,
        output_csm=defaults.output_csm,
        output_coils=defaults.output_coils
    )
    args = parser.parse_args()
    generate_cartesian_phantom(
        args.output,
        args.coils,
        args.matrix,
        args.repetitions,
        args.acceleration,
        args.oversampling,
        args.noise_level,
        args.calibration_width,
        args.noise_calibration,
        args.store_coordinates,
        args.output_phantom,
        args.output_csm,
        args.output_coils
    )
