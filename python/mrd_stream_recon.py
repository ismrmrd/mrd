import argparse
from typing import BinaryIO, Iterable, Union
import sys
import mrd
import numpy as np
from transform import k2i

def acquisition_reader(input: Iterable[mrd.StreamItem]) -> Iterable[mrd.Acquisition]:
    for item in input:
        _, item_data = item
        if not isinstance(item_data, mrd.Acquisition):
            continue
        yield item_data

def stream_item_sink(input: Iterable[Union[mrd.Acquisition, mrd.Image[np.float32]]]) -> Iterable[mrd.StreamItem]:
    for item in input:
        if isinstance(item, mrd.Acquisition):
            yield ('Acquisition', item)
        elif isinstance(item, mrd.Image) and item.data.dtype == np.float32:
            yield ('Image<float32>', item)
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
            xline = k2i(acq.data, [1])
            x0 = int((eNx - rNx) / 2)
            x1 = int((eNx - rNx) / 2 + rNx)
            xline = xline[:, x0:x1]
            acq.center_sample = int(rNx/2)
            acq.data = xline.astype('complex64')  # Keep it in image space

        yield acq

def accumulate_fft(head: mrd.Header, input: Iterable[mrd.Acquisition]) -> Iterable[mrd.Image[np.float32]]:
    enc = head.encoding[0]

    # Matrix size
    if enc.encoded_space and enc.recon_space and enc.encoded_space.matrix_size and enc.recon_space.matrix_size:
        eNx = enc.encoded_space.matrix_size.x
        eNy = enc.encoded_space.matrix_size.y
        eNz = enc.encoded_space.matrix_size.z
        rNx = enc.recon_space.matrix_size.x
    else:
        raise Exception('Required encoding information not found in header')

    # Number of Slices, Reps, Contrasts, etc.
    ncoils = 1
    if head.acquisition_system_information and head.acquisition_system_information.receiver_channels:
        ncoils = head.acquisition_system_information.receiver_channels

    if enc.encoding_limits and enc.encoding_limits.slice != None:
        nslices = enc.encoding_limits.slice.maximum + 1
    else:
        nslices = 1

    ncontrasts = 1
    if enc.encoding_limits and enc.encoding_limits.contrast != None:
        ncontrasts = enc.encoding_limits.contrast.maximum + 1

    if enc.encoding_limits and enc.encoding_limits.kspace_encoding_step_1 != None:
        ky_offset = int((eNy+1)/2) - enc.encoding_limits.kspace_encoding_step_1.center
    else:
        ky_offset = 0

    current_rep = -1
    reference_acquisition = None
    buffer = None
    mask = None

    def produce_image(buffer: np.ndarray, ref_acq: mrd.Acquisition) -> Iterable[mrd.Image[np.float32]]:
        if buffer.shape[-3] > 1:
            img = k2i(buffer, dim=[-2, -3])  # Assuming FFT in x-direction has happened upstream
        else:
            img = k2i(buffer, dim=[-2])  # Assuming FFT in x-direction has happened upstream

        for contrast in range(img.shape[0]):
            for islice in range(img.shape[1]):
                img_combined = np.sqrt(np.abs(np.sum(img[contrast, islice] * np.conj(img[contrast, islice]), axis=0)).astype('float32'))
                img_combined = np.reshape(img_combined, (1,1,img_combined.shape[-2], img_combined.shape[-1]))
                mrd_image = mrd.Image[np.float32](image_type=mrd.ImageType.MAGNITUDE, data=img_combined)
                yield mrd_image

    for acq in input:
        if acq.idx.repetition != current_rep:
            # If we have a current buffer pass it on
            if buffer is not None and reference_acquisition is not None:
                yield from produce_image(buffer, reference_acquisition)

            # Reset buffer
            if acq.data.shape[-1] == eNx:
                readout_length = eNx
            else:
                readout_length = rNx  # Readout oversampling has probably been removed upstream

            buffer = np.zeros((ncontrasts, nslices, ncoils, eNz, eNy, readout_length), dtype=np.complex64)
            current_rep = acq.idx.repetition
            reference_acquisition = acq

        # Stuff into the buffer
        if buffer is not None:
            contrast = acq.idx.contrast if acq.idx.contrast is not None else 0
            slice = acq.idx.slice if acq.idx.slice is not None else 0
            k1 = acq.idx.kspace_encode_step_1 if acq.idx.kspace_encode_step_1 is not None else 0
            k2 = acq.idx.kspace_encode_step_2 if acq.idx.kspace_encode_step_2 is not None else 0
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
