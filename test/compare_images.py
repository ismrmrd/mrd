import sys
import argparse

import numpy as np
from PIL import Image

import mrd


def diff(ref, img):
    diff = img - ref
    rmse = np.sqrt(np.mean(np.square(diff)))
    return rmse

def get_data(name):
    images = []
    with mrd.BinaryMrdReader(name) as r:
        header = r.read_header()
        for item in r.read_data():
            if not isinstance(item, mrd.StreamItem.ImageFloat):
                raise RuntimeError("Stream must contain only floating point images")
            image = item.value
            images.append(image.data)
    return images

def error(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Compares MRD images")
    parser.add_argument('input', nargs="+", type=str, help="Input files")
    args = parser.parse_args()

    threshold = .000001
    save_diff = False

    refname = args.input[0]
    ref_imgs = get_data(refname)

    for fname in args.input:
        test_imgs = get_data(fname)
        if len(test_imgs) != len(ref_imgs):
            error(f"{refname} and {fname} have different number of images")

        for (ref, img,) in zip(ref_imgs, test_imgs):
            err = diff(ref, img)
            if err > threshold:
                if save_diff:
                    errimg = (img-ref)[0,0]
                    errimg /= np.amax(errimg)
                    errimg *= 255
                    Image.fromarray(errimg.astype(np.uint8)).save(f"{n}.png")
                error(f"{refname} and {fname} differ by {err}")


if __name__ == "__main__":
    main()
