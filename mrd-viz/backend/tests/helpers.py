from __future__ import annotations

from pathlib import Path

import mrd
import numpy as np


def write_image_mrd(path: Path, arrays: list[np.ndarray]) -> None:
    with mrd.BinaryMrdWriter(str(path)) as writer:
        writer.write_header(mrd.Header())
        writer.write_data([_image_item(array, image_index) for image_index, array in enumerate(arrays)])


def write_header_only_mrd(path: Path) -> None:
    with mrd.BinaryMrdWriter(str(path)) as writer:
        writer.write_header(mrd.Header())
        writer.write_data([])


def _image_item(array: np.ndarray, image_index: int) -> mrd.StreamItem.ImageFloat:
    data = np.asarray(array, dtype=np.float32)
    head = mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE)
    head.image_index = image_index
    head.field_of_view[:] = [float(data.shape[-1]), float(data.shape[-2]), 1.0]
    image = mrd.Image[np.float32](head=head, data=data)
    return mrd.StreamItem.ImageFloat(image)