import argparse
import numpy as np
import numpy.typing as npt
import mrd

def verify_basic_recon(reference_file: str, testdata_file: str):
    reference: npt.NDArray[np.float32]
    with mrd.BinaryMrdReader(reference_file) as reader:
        header = reader.read_header()
        assert header is not None, "No header found in reference data"

        eNx = header.encoding[0].encoded_space.matrix_size.x
        rNx = header.encoding[0].recon_space.matrix_size.x

        coil_images = None
        for item in reader.read_data():
            if isinstance(item, mrd.StreamItem.ArrayComplexFloat):
                coil_images = np.squeeze(item.value)

        assert coil_images is not None, "No coil images found in reference data"
        reference = np.sqrt(np.abs(np.sum(coil_images * np.conj(coil_images), 0)))

        ro_length = reference.shape[-1]
        assert ro_length == eNx

        if eNx != rNx:
            # Crop the reference to the reconstruction size
            offset = (ro_length - rNx) // 2
            reference = reference[:, offset:offset+rNx]

    images = []
    with mrd.BinaryMrdReader(testdata_file) as reader:
        reader.read_header()
        for item in reader.read_data():
            if isinstance(item, mrd.StreamItem.ImageFloat):
                images.append(item.value)

    assert len(images) > 0, "No images found in testdata"

    for image in images:
        reconstruction = np.squeeze(image.data)
        assert np.linalg.norm(reconstruction - reference) / np.linalg.norm(reference) < 2e-5


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate results of an ismrmrd reconstruction')
    parser.add_argument('--reference', type=str, help='Reference file', required=True)
    parser.add_argument('--testdata', type=str, help='Test data file', required=True)
    args = parser.parse_args()
    verify_basic_recon(args.reference, args.testdata)
