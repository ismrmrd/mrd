"""Convert fastMRI HDF5 files to MRD format."""

import argparse
import logging

import h5py
import ismrmrd
import mrd
import numpy as np
from mrd.tools.ismrmrd_to_mrd import convert_header

FASTMRI_DATASET_NAME_HEADER = "ismrmrd_header"
FASTMRI_DATASET_NAME_KSPACE = "kspace"
FASTMRI_DATASET_NAME_MASK = "mask"
FASTMRI_DATASET_NAME_RECON_RSS = "reconstruction_rss"
FASTMRI_DATASET_NAME_RECON_ESC = "reconstruction_esc"

logger = logging.getLogger(__name__)


def _reconcile_slice_count(encoding_limits: mrd.EncodingLimitsType, num_slices: int, kind: str) -> None:
    """Warn and rewrite ``encoding_limits.slice`` when it disagrees with the dataset."""
    header_slices = 1
    if encoding_limits.slice is not None:
        header_slices = encoding_limits.slice.maximum - encoding_limits.slice.minimum + 1
    if num_slices == header_slices:
        return
    logger.warning(
        f"{kind} dataset has {num_slices} slice(s) but header advertises {header_slices}; "
        f"using the dataset count and correcting encoding_limits.slice in the output header."
    )
    old_min = encoding_limits.slice.minimum if encoding_limits.slice is not None else 0
    old_center = encoding_limits.slice.center if encoding_limits.slice is not None else old_min + num_slices // 2
    new_max = old_min + num_slices - 1
    new_center = max(old_min, min(old_center, new_max))
    encoding_limits.slice = mrd.LimitType(minimum=old_min, maximum=new_max, center=new_center)


def _detect_spatial_axes_swap(
    actual_last_two: tuple[int, ...],
    expected_xy: tuple[int, int],
    kind: str,
    axis_label: str,
) -> bool:
    """Return True iff the last two dataset dims are transposed relative to ``expected_xy``."""
    x, y = expected_xy
    if tuple(actual_last_two) == (x, y):
        return False
    if tuple(actual_last_two) == (y, x):
        logger.warning(
            f"{kind} dataset shape ends with {tuple(actual_last_two)} which has {axis_label} "
            f"axes swapped relative to the fastMRI spec (..., {x}, {y}); reading with transposed indexing."
        )
        return True
    raise RuntimeError(
        f"{kind} dataset spatial dims {tuple(actual_last_two)} do not match expected matrix size "
        f"({x}, {y}) in either order."
    )


def _require_dataset(f: h5py.File, name: str) -> h5py.Dataset:
    """Fetch ``f[name]`` and assert it is an ``h5py.Dataset``."""
    dset = f[name]
    if not isinstance(dset, h5py.Dataset):
        raise RuntimeError(f"Expected dataset '{name}' to be a h5py.Dataset, but got {type(dset)}")
    return dset


def extract_and_convert_header(dset: h5py.Dataset) -> mrd.Header:
    """Extract ISMRMRD header from fastMRI dataset and convert to MRD header."""
    header_bytes = dset[()]
    ismrmrd_header = ismrmrd.xsd.CreateFromDocument(header_bytes)
    mrd_header = convert_header(ismrmrd_header)
    return mrd_header


def convert_kspace(dset: h5py.Dataset, mrd_header: mrd.Header, output_data_filename: str) -> None:
    """Extract k-space data from fastMRI dataset and write acquisitions to MRD file."""
    header_channels = 1
    if mrd_header.acquisition_system_information is not None:
        if mrd_header.acquisition_system_information.receiver_channels is not None:
            header_channels = mrd_header.acquisition_system_information.receiver_channels

    if len(mrd_header.encoding) < 1:
        raise RuntimeError("MRD header must contain at least one encoding to convert k-space data")
    encoding: mrd.EncodingType = mrd_header.encoding[0]
    if encoding.encoded_space is None:
        raise RuntimeError("MRD header encoding must contain encoded_space to convert k-space data")
    encoded_space = encoding.encoded_space
    if encoding.encoding_limits is None:
        raise RuntimeError("MRD header encoding must contain encoding_limits to convert k-space data")
    encoding_limits = encoding.encoding_limits

    # The fastMRI spec stores k-space as (slices, [channels,] kx, ky) where kx == matrix_size.x
    # (readout, often oversampled) and ky == matrix_size.y (phase encode). Trust the dataset
    # shape for slice/channel counts (fastMRI brain files often contain only a subset of the
    # slices advertised in the header) and accept files that swap the last two axes (Siemens
    # twix dumps repackaged into the fastMRI layout).
    if dset.ndim not in (3, 4):
        raise RuntimeError(f"Expected k-space dataset to be 3D or 4D, but got shape {dset.shape}")

    # fastMRI axis layout: 4-D = (slice, channel, kx, ky); 3-D = (slice, kx, ky) for single-coil
    # "esc" files. Slice is always axis 0; the spatial (kx, ky) pair is always the trailing two.
    num_slices = dset.shape[0]
    num_channels = dset.shape[1] if dset.ndim == 4 else 1

    _reconcile_slice_count(encoding_limits, num_slices, "K-space")
    if dset.ndim == 4 and num_channels != header_channels:
        logger.warning(
            f"K-space dataset has {num_channels} channel(s) but header advertises {header_channels}; "
            f"using the dataset count and correcting acquisition_system_information.receiver_channels "
            f"in the output header."
        )
        if mrd_header.acquisition_system_information is None:
            mrd_header.acquisition_system_information = mrd.AcquisitionSystemInformationType()
        mrd_header.acquisition_system_information.receiver_channels = num_channels
        # Trim coil labels if the header advertised more coils than the data contains; leave
        # alone if shorter, since we have no label information to fabricate.
        coil_labels = mrd_header.acquisition_system_information.coil_label
        if coil_labels is not None and len(coil_labels) > num_channels:
            mrd_header.acquisition_system_information.coil_label = coil_labels[:num_channels]

    mx, my = encoded_space.matrix_size.x, encoded_space.matrix_size.y
    axes_swapped = _detect_spatial_axes_swap(dset.shape[-2:], (mx, my), "K-space", "readout/phase-encode")

    # The fastMRI dataset is zero-padded along the phase-encode axis out to matrix_size.y;
    # the actually-acquired lines occupy a central window described by encoding_limits.
    num_kspace_lines = my
    e1_offset = 0
    if encoding_limits.kspace_encoding_step_1 is not None:
        e1_count = encoding_limits.kspace_encoding_step_1.maximum - encoding_limits.kspace_encoding_step_1.minimum + 1
        if e1_count < my:
            e1_offset = my // 2 - encoding_limits.kspace_encoding_step_1.center
            num_kspace_lines = e1_count

    with mrd.BinaryMrdWriter(output_data_filename) as writer:
        writer.write_header(mrd_header)

        scan_counter = 0

        def _new_acquisition(slice: int, line: int) -> mrd.Acquisition:
            """Create a new acquisition for the given slice and k-space line."""
            nonlocal scan_counter
            head = mrd.AcquisitionHeader()
            head.scan_counter = scan_counter
            scan_counter += 1
            head.channel_order = list(range(num_channels))
            head.center_sample = encoded_space.matrix_size.x // 2
            head.encoding_space_ref = 0
            head.position[:] = [0.0, 0.0, 0.0]
            head.read_dir[:] = [1.0, 0.0, 0.0]
            head.phase_dir[:] = [0.0, 1.0, 0.0]
            head.slice_dir[:] = [0.0, 0.0, 1.0]

            head.idx.slice = slice
            head.idx.kspace_encode_step_1 = line

            e1 = line + e1_offset
            if dset.ndim == 4:
                if axes_swapped:
                    # Dataset axes are (slices, channels, ky, kx)
                    data = dset[slice, :, e1, :]
                else:
                    data = dset[slice, :, :, e1]
            else:
                if axes_swapped:
                    # Dataset axes are (slices, ky, kx)
                    data = dset[slice, e1, :]
                else:
                    data = dset[slice, :, e1]
                data = np.expand_dims(data, axis=0)  # add channel dimension

            acq = mrd.Acquisition(head=head, data=data)
            return acq

        # Synthesize noise acquisitions using first or last line of k-space, which should not have any signal
        for slice in range(num_slices):
            first_line = _new_acquisition(slice, 0)
            last_line = _new_acquisition(slice, num_kspace_lines - 1)

            # Choose the line with lower std as the noise acquisition, since some datasets have interference in k-space
            first_line_std = np.std(np.abs(first_line.data))
            last_line_std = np.std(np.abs(last_line.data))
            if last_line_std < first_line_std:
                acq = last_line
                acq_std = last_line_std
            else:
                acq = first_line
                acq_std = first_line_std

            acq.head.flags = mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT
            if acq_std >= 1e-5:
                logger.warning(f"Expected to find noise in slice {slice}, but data has significant variation with std {acq_std}.")
            item = mrd.StreamItem.Acquisition(acq)
            writer.write_data([item])

        # Extract and write k-space acquisitions
        for slice in range(num_slices):
            for line in range(num_kspace_lines):
                acq = _new_acquisition(slice, line)
                item = mrd.StreamItem.Acquisition(acq)
                writer.write_data([item])


def write_images(dset: h5py.Dataset, mrd_header: mrd.Header, output_images_filename: str) -> None:
    """Extract reconstructed images from fastMRI dataset and write to MRD file."""
    if len(mrd_header.encoding) < 1:
        raise RuntimeError("MRD header must contain at least one encoding to convert images")
    encoding: mrd.EncodingType = mrd_header.encoding[0]
    if encoding.recon_space is None:
        raise RuntimeError("MRD header encoding must contain recon_space to convert images")
    recon_space = encoding.recon_space
    if encoding.encoding_limits is None:
        raise RuntimeError("MRD header encoding must contain encoding_limits to convert images")
    encoding_limits = encoding.encoding_limits

    if dset.ndim != 3:
        raise RuntimeError(f"Expected image dataset to be 3D, but got shape {dset.shape}")

    num_slices = dset.shape[0]
    _reconcile_slice_count(encoding_limits, num_slices, "Image")

    rx, ry = recon_space.matrix_size.x, recon_space.matrix_size.y
    axes_swapped = _detect_spatial_axes_swap(dset.shape[-2:], (rx, ry), "Image", "row/column")

    with mrd.BinaryMrdWriter(output_images_filename) as writer:
        writer.write_header(mrd_header)

        for slice in range(num_slices):
            head = mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE)
            head.field_of_view[:] = [
                recon_space.field_of_view_mm.x,
                recon_space.field_of_view_mm.y,
                recon_space.field_of_view_mm.z,
            ]
            head.position[:] = [0.0, 0.0, 0.0]
            head.col_dir[:] = [1.0, 0.0, 0.0]
            head.line_dir[:] = [0.0, 1.0, 0.0]
            head.slice_dir[:] = [0.0, 0.0, 1.0]
            head.slice = slice
            head.image_index = slice
            head.image_series_index = 1

            # MRD images are of shape (channels, slices, rows, cols)
            # In the fastMRI spec axes are (slice, x, y); rows/cols are (y, x), so transpose.
            # If the input file already stores (slice, y, x), no transpose is needed.
            if axes_swapped:
                data = dset[slice, :, :]
            else:
                data = np.transpose(dset[slice, :, :], (1, 0))
            data = np.expand_dims(data, axis=(0, 1))
            data = np.ascontiguousarray(data)
            img = mrd.Image(head=head, data=data)
            item = mrd.StreamItem.ImageFloat(img)
            writer.write_data([item])


def convert(input_filename: str, output_data_filename: str | None, output_images_filename: str | None) -> None:
    """Convert fastMRI HDF5 file to MRD format."""
    with h5py.File(input_filename, "r") as f:
        # First validate the input file
        required_datasets = [FASTMRI_DATASET_NAME_HEADER]
        if output_data_filename is not None:
            required_datasets += [FASTMRI_DATASET_NAME_KSPACE]
        if output_images_filename is not None:
            required_datasets += [FASTMRI_DATASET_NAME_RECON_RSS]

        for dset_name in required_datasets:
            if dset_name not in f:
                raise RuntimeError(f"Input file is missing required dataset '{dset_name}'")

        # Convert ISMRMRD header to MRD header
        mrd_header = extract_and_convert_header(_require_dataset(f, FASTMRI_DATASET_NAME_HEADER))

        # Convert and write k-space data if requested
        if output_data_filename is not None:
            convert_kspace(_require_dataset(f, FASTMRI_DATASET_NAME_KSPACE), mrd_header, output_data_filename)

        # Convert and write images if requested
        if output_images_filename is not None:
            write_images(_require_dataset(f, FASTMRI_DATASET_NAME_RECON_RSS), mrd_header, output_images_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert fastMRI HDF5 files to MRD format.")

    parser.add_argument("-i", "--input", type=str, required=True, help="Input fastMRI HDF5 file")
    parser.add_argument("-od", "--output-data", type=str, help="Output MRD file for k-space data")
    parser.add_argument("-oi", "--output-images", type=str, help="Output MRD file for reconstructed images")

    args = parser.parse_args()

    if args.output_data is None and args.output_images is None:
        parser.error("At least one of --output-data or --output-images must be specified")

    convert(args.input, args.output_data, args.output_images)
