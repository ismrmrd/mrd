import warnings
import numpy as np
from numpy.fft import fftshift, ifftshift, fftn, ifftn

def k2i(k: np.ndarray, dim=None, img_shape=None) -> np.ndarray:
    if not dim:
        dim = range(k.ndim)
    img = fftshift(ifftn(ifftshift(k, axes=dim), s=img_shape, axes=dim), axes=dim)
    img *= np.sqrt(np.prod(np.take(img.shape, dim)))
    return img


def i2k(img: np.ndarray, dim=None, k_shape=None) -> np.ndarray:
    if not dim:
        dim = range(img.ndim)

    k = fftshift(fftn(ifftshift(img, axes=dim), s=k_shape, axes=dim), axes=dim)
    k /= np.sqrt(np.prod(np.take(img.shape, dim)))
    return k
