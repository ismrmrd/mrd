import sys
import argparse
import numpy as np
from typing import BinaryIO, Iterable, Union

import mrd
from mrd.tools.transform import kspace_to_image, image_to_kspace


def acquisition_reader(input: Iterable[mrd.StreamItem]) -> Iterable[mrd.Acquisition]:
    for item in input:
        if not isinstance(item, mrd.StreamItem.Acquisition):
            # Skip non-acquisition items
            continue
        if item.value.head.flags & mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT:
            # Currently ignoring noise scans
            continue
        yield item.value

def stream_item_sink(input: Iterable[Union[mrd.Acquisition, mrd.Image[np.float32]]]) -> Iterable[mrd.StreamItem]:
    for item in input:
        if isinstance(item, mrd.Acquisition):
            yield mrd.StreamItem.Acquisition(item)
        elif isinstance(item, mrd.Image) and item.data.dtype == np.float32:
            yield mrd.StreamItem.ImageFloat(item)
        else:
            raise ValueError("Unknown item type")

def remove_oversampling(head: mrd.Header,input: Iterable[mrd.Acquisition]) -> Iterable[mrd.Acquisition]:
    enc = head.encoding[0]

    if enc.encoded_space and enc.encoded_space.matrix_size and enc.recon_space and enc.recon_space.matrix_size:
        eNx = enc.encoded_space.matrix_size.x
        rNx = enc.recon_space.matrix_size.x
    else:
        raise Exception('Encoding information missing from header')

    for acq in input:
        if eNx != rNx and acq.samples() == eNx:
            xline = kspace_to_image(acq.data, [1])
            x0 = (eNx - rNx) // 2
            x1 = x0 + rNx
            xline = xline[:, x0:x1]
            acq.head.center_sample = rNx // 2
            acq.data = image_to_kspace(xline, [1])
        yield acq

def accumulate_fft(head: mrd.Header, input: Iterable[mrd.Acquisition]) -> Iterable[mrd.Image[np.float32]]:
    enc = head.encoding[0]

    # Matrix size
    if enc.encoded_space and enc.recon_space and enc.encoded_space.matrix_size and enc.recon_space.matrix_size:
        eNx = enc.encoded_space.matrix_size.x
        eNy = enc.encoded_space.matrix_size.y
        eNz = enc.encoded_space.matrix_size.z
        rNx = enc.recon_space.matrix_size.x
        rNy = enc.recon_space.matrix_size.y
        rNz = enc.recon_space.matrix_size.z
    else:
        raise Exception('Required encoding information not found in header')

    # Field of view
    if enc.recon_space and enc.recon_space.field_of_view_mm:
        rFOVx = enc.recon_space.field_of_view_mm.x
        rFOVy = enc.recon_space.field_of_view_mm.y
        rFOVz = enc.recon_space.field_of_view_mm.z if enc.recon_space.field_of_view_mm.z else 1
    else:
        raise Exception('Required field of view information not found in header')

    # Number of Slices, Reps, Contrasts, etc.
    ncoils = 1
    if head.acquisition_system_information and head.acquisition_system_information.receiver_channels:
        ncoils = head.acquisition_system_information.receiver_channels

    nslices = 1
    if enc.encoding_limits and enc.encoding_limits.slice != None:
        nslices = enc.encoding_limits.slice.maximum + 1

    ncontrasts = 1
    if enc.encoding_limits and enc.encoding_limits.contrast != None:
        ncontrasts = enc.encoding_limits.contrast.maximum + 1

    ky_offset = 0
    if enc.encoding_limits and enc.encoding_limits.kspace_encoding_step_1 != None:
        ky_offset = int((eNy+1)/2) - enc.encoding_limits.kspace_encoding_step_1.center

    current_rep = -1
    reference_acquisition = None
    buffer = None
    image_index = 0

    def produce_image(buffer: np.ndarray, ref_acq: mrd.Acquisition) -> Iterable[mrd.Image[np.float32]]:
        nonlocal image_index

        if buffer.shape[-3] > 1:
            img = kspace_to_image(buffer, dim=[-1, -2, -3])
        else:
            img = kspace_to_image(buffer, dim=[-1, -2])

        for contrast in range(img.shape[0]):
            for islice in range(img.shape[1]):
                slice = img[contrast, islice]
                combined = np.squeeze(np.sqrt(np.abs(np.sum(slice * np.conj(slice), axis=0)).astype('float32')))

                xoffset = (combined.shape[-1] + 1) // 2 - (rNx+1) // 2
                yoffset = (combined.shape[-2] + 1) // 2 - (rNy+1) // 2
                if len(combined.shape) == 3:
                    zoffset = (combined.shape[-3] + 1) // 2 - (rNz+1) // 2
                    combined = combined[zoffset:(zoffset+rNz), yoffset:(yoffset+rNy), xoffset:(xoffset+rNx)]
                    combined = np.reshape(combined, (1, combined.shape[-3], combined.shape[-2], combined.shape[-1]))
                elif len(combined.shape) == 2:
                    combined = combined[yoffset:(yoffset+rNy), xoffset:(xoffset+rNx)]
                    combined = np.reshape(combined, (1, 1, combined.shape[-2], combined.shape[-1]))
                else:
                    raise Exception('Array img_combined should have 2 or 3 dimensions')

                imghdr = mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE)
                imghdr.measurement_uid = ref_acq.head.measurement_uid
                imghdr.field_of_view[0] = rFOVx
                imghdr.field_of_view[1] = rFOVy
                imghdr.field_of_view[2] = rFOVz/rNz
                imghdr.position = ref_acq.head.position
                imghdr.col_dir = ref_acq.head.read_dir
                imghdr.line_dir = ref_acq.head.phase_dir
                imghdr.slice_dir = ref_acq.head.slice_dir
                imghdr.patient_table_position = ref_acq.head.patient_table_position
                imghdr.average = ref_acq.head.idx.average
                imghdr.slice = ref_acq.head.idx.slice
                imghdr.contrast = contrast
                imghdr.phase = ref_acq.head.idx.phase
                imghdr.repetition = ref_acq.head.idx.repetition
                imghdr.set = ref_acq.head.idx.set
                imghdr.acquisition_time_stamp = ref_acq.head.acquisition_time_stamp
                imghdr.physiology_time_stamp = ref_acq.head.physiology_time_stamp
                imghdr.image_index = image_index
                image_index += 1

                mrd_image = mrd.Image[np.float32](head=imghdr, data=combined)
                yield mrd_image

    for acq in input:
        if acq.head.idx.repetition != current_rep:
            # If we have a current buffer pass it on
            if buffer is not None and reference_acquisition is not None:
                yield from produce_image(buffer, reference_acquisition)

            # Reset buffer
            if acq.data.shape[-1] == eNx:
                readout_length = eNx
            else:
                readout_length = rNx  # Readout oversampling has been removed upstream

            buffer = np.zeros((ncontrasts, nslices, ncoils, eNz, eNy, readout_length), dtype=np.complex64)
            current_rep = acq.head.idx.repetition
            reference_acquisition = acq

        # Stuff into the buffer
        if buffer is not None:
            contrast = acq.head.idx.contrast if acq.head.idx.contrast is not None else 0
            slice = acq.head.idx.slice if acq.head.idx.slice is not None else 0
            k1 = acq.head.idx.kspace_encode_step_1 if acq.head.idx.kspace_encode_step_1 is not None else 0
            k2 = acq.head.idx.kspace_encode_step_2 if acq.head.idx.kspace_encode_step_2 is not None else 0
            buffer[contrast, slice, :, k2, k1 + ky_offset, :] = acq.data

    if buffer is not None and reference_acquisition is not None:
        yield from produce_image(buffer, reference_acquisition)
        buffer = None
        reference_acquisition = None

def reconstruct_mrd_stream(input: BinaryIO, output: BinaryIO):
    with mrd.BinaryMrdReader(input) as reader:
        with mrd.BinaryMrdWriter(output) as writer:
            head = reader.read_header()
            if head is None:
                raise Exception("Could not read header")
            writer.write_header(head)
            writer.write_data(
                stream_item_sink(
                    accumulate_fft(head,
                        remove_oversampling(head,
                            acquisition_reader(reader.read_data())))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstructs an MRD stream")
    parser.add_argument('-i', '--input', type=str, required=False, help="Input file, defaults to stdin")
    parser.add_argument('-o', '--output', type=str, required=False, help="Output file, defaults to stdout")
    args = parser.parse_args()

    input = open(args.input, "rb") if args.input is not None else sys.stdin.buffer
    output = open(args.output, "wb") if args.output is not None else sys.stdout.buffer

    reconstruct_mrd_stream(input, output)
