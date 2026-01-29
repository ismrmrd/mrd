import ctypes
import h5py

import numpy as np
import ismrmrd
import mrd


# input_filename = "singlecoil.file1000001.h5"
input_filename = "multicoil.file1000001.h5"
output_data_filename = "file1000001.data.mrd"
output_images_filename = "file1000001.images.mrd"

f = h5py.File(input_filename, "r")

dset = f["ismrmrd_header"]
header_bytes = dset[()]

ismrmrd_header = ismrmrd.xsd.CreateFromDocument(header_bytes)
print(ismrmrd_header)

from mrd.tools.ismrmrd_to_mrd import convert_header
mrd_header = convert_header(ismrmrd_header)

num_channels = 1
if mrd_header.acquisition_system_information is not None:
    if mrd_header.acquisition_system_information.receiver_channels is not None:
        num_channels = mrd_header.acquisition_system_information.receiver_channels

assert len(mrd_header.encoding) >= 1
encoding: mrd.EncodingType = mrd_header.encoding[0]
assert encoding.encoded_space is not None
assert encoding.recon_space is not None
encoded_space = encoding.encoded_space
recon_space = encoding.recon_space

assert encoded_space.matrix_size is not None
assert recon_space.matrix_size is not None

assert encoding.encoding_limits is not None
encoding_limits = encoding.encoding_limits

num_slices = 1
if encoding_limits.slice is not None:
    num_slices = encoding_limits.slice.maximum - encoding_limits.slice.minimum + 1

e1_offset = 0
num_kspace_lines = encoded_space.matrix_size.y
if encoding_limits.kspace_encoding_step_1 is not None:
    e1_count = encoding_limits.kspace_encoding_step_1.maximum - encoding_limits.kspace_encoding_step_1.minimum + 1
    if e1_count < encoded_space.matrix_size.y:
        e1_offset = num_kspace_lines // 2 - encoding_limits.kspace_encoding_step_1.center
        num_kspace_lines = e1_count

dset: h5py.Dataset = f["kspace"]
if dset.ndim == 4:
    assert dset.shape == (num_slices, num_channels, encoded_space.matrix_size.x, encoded_space.matrix_size.y)
else:
    num_channels = 1
    assert dset.shape == (num_slices, encoded_space.matrix_size.x, encoded_space.matrix_size.y)

with mrd.BinaryMrdWriter(output_data_filename) as writer:
    writer.write_header(mrd_header)

    scan_counter = 0

    # Synthesize noise acquisitions
    # We'll just use the first line of k-space, which should not have any signal
    for slice in range(num_slices):
        head = mrd.AcquisitionHeader()
        head.flags = mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT
        head.scan_counter = scan_counter
        scan_counter += 1
        head.channel_order = list(range(num_channels))
        head.center_sample = encoded_space.matrix_size.x // 2 # TODO: Is this true for all fastmri data?
        head.position[:] = [0.0, 0.0, 0.0]
        head.read_dir[:] = [1.0, 0.0, 0.0]
        head.phase_dir[:] = [0.0, 1.0, 0.0]
        head.slice_dir[:] = [0.0, 0.0, 1.0]

        head.idx.slice = slice
        head.idx.kspace_encode_step_1 = 0

        e1 = 0 + e1_offset
        if dset.ndim == 4:
            data = dset[slice, :, :, e1]
        else:
            data = dset[slice, :, e1]
            data = np.expand_dims(data, axis=0)  # add channel dimension

        assert np.std(np.abs(data)) < 1e-5, "Expected to find noise, but data has significant variation"
        acq = mrd.Acquisition(head=head, data=data)
        item = mrd.StreamItem.Acquisition(acq)
        writer.write_data([item])

    for slice in range(num_slices):
        for line in range(num_kspace_lines):
            head = mrd.AcquisitionHeader()
            head.scan_counter = scan_counter
            scan_counter += 1
            head.channel_order = list(range(num_channels))
            head.center_sample = encoded_space.matrix_size.x // 2 # TODO: Is this true for all fastmri data?
            head.position[:] = [0.0, 0.0, 0.0]
            head.read_dir[:] = [1.0, 0.0, 0.0]
            head.phase_dir[:] = [0.0, 1.0, 0.0]
            head.slice_dir[:] = [0.0, 0.0, 1.0]

            head.idx.slice = slice
            head.idx.kspace_encode_step_1 = line

            e1 = line + e1_offset
            if dset.ndim == 4:
                data = dset[slice, :, :, e1]
            else:
                data = dset[slice, :, e1]
                data = np.expand_dims(data, axis=0)  # add channel dimension
            acq = mrd.Acquisition(head=head, data=data)
            item = mrd.StreamItem.Acquisition(acq)
            writer.write_data([item])


dset = f["reconstruction_rss"]
assert dset.shape == (num_slices, recon_space.matrix_size.x, recon_space.matrix_size.y)

with mrd.BinaryMrdWriter(output_images_filename) as writer:
    writer.write_header(mrd_header)

    for slice in range(num_slices):
        head = mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE)
        head.field_of_view[:] = [recon_space.field_of_view_mm.x, recon_space.field_of_view_mm.y, recon_space.field_of_view_mm.z]
        head.position[:] = [0.0, 0.0, 0.0]
        head.col_dir[:] = [1.0, 0.0, 0.0]
        head.line_dir[:] = [0.0, 1.0, 0.0]
        head.slice_dir[:] = [0.0, 0.0, 1.0]
        head.slice = slice
        head.image_index = slice
        head.image_series_index = 1

        data = np.transpose(dset[slice, :, :], (1, 0))
        data = np.expand_dims(data, axis=(0, 1))
        img = mrd.Image(head=head, data=data)
        item = mrd.StreamItem.ImageFloat(img)
        writer.write_data([item])
