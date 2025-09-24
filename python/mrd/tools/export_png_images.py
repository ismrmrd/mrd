import sys
import argparse
import numpy as np
from PIL import Image

import mrd


def export(input, output, verbose=False):
    with mrd.BinaryMrdReader(input) as r:
        header = r.read_header()
        image_count = 0
        for item in r.read_data():
            if not isinstance(item, mrd.StreamItem.ImageFloat):
                raise RuntimeError("Stream must contain only floating point images")

            image = item.value
            image.data *= 255 / image.data.max()
            pixels = image.data.astype(np.uint8)

            for c in range(image.channels()):
                for s in range(image.slices()):
                    im = Image.fromarray(pixels[c, s, :, :], 'L')
                    filename = f"{output}{image_count:05d}.png"
                    im.save(filename, format='PNG')
                    if verbose:
                        print(f"Generated image {filename}")
                    image_count += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstructs an MRD stream")
    parser.add_argument('-i', '--input', type=str, required=False,
                        help="Input file (default stdin)")
    parser.add_argument('-o', '--output-prefix', type=str, required=False,
                        help="Output filename prefix", default="image_")
    parser.add_argument('-v', '--verbose', action='store_true', help="Print progress to stderr")
    args = parser.parse_args()

    input = open(args.input, "rb") if args.input is not None else sys.stdin.buffer

    export(input, args.output_prefix, args.verbose)
