from __future__ import annotations

# Synthetic array tests are the fastest guardrail for rendering semantics. They
# keep normalization, representative-plane selection, and unsupported-shape
# behavior pinned without paying the cost or fragility of writing MRD files.

import mrd
import numpy as np
import pytest

from mrd_viz.main import PreviewOptions, _display_plane, _image_tile, _normalize_to_uint8, _plane_to_png_base64


def test_display_plane_selects_representative_plane() -> None:
    assert _display_plane(np.ones((3, 4))).shape == (3, 4)
    assert _display_plane(np.ones((2, 3, 4))).shape == (3, 4)
    assert _display_plane(np.ones((5, 2, 3, 4))).shape == (3, 4)


def test_normalize_handles_constant_complex_and_range() -> None:
    assert np.all(_normalize_to_uint8(np.ones((2, 2), dtype=np.float32)) == 0)

    complex_pixels = _normalize_to_uint8(np.array([[0 + 0j, 3 + 4j]], dtype=np.complex64))
    assert complex_pixels.tolist() == [[0, 255]]

    ranged_pixels = _normalize_to_uint8(np.array([[-1.0, 1.0]], dtype=np.float32))
    assert ranged_pixels.tolist() == [[0, 255]]


def test_png_thumbnail_is_bounded() -> None:
    payload, shape = _plane_to_png_base64(np.arange(64, dtype=np.float32).reshape(8, 8), thumbnail=True, max_size=4)

    assert payload.startswith("iVBOR")
    assert shape == [4, 4]


def test_unsupported_image_shape_becomes_nonrenderable_tile() -> None:
    image = mrd.Image[np.float32](
        head=mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE),
        data=np.zeros((1, 1, 1, 2, 2), dtype=np.float32),
    )

    tile = _image_tile(image, "ImageFloat", stream_index=0, image_index=0, options=PreviewOptions(max_thumbnails=1))

    assert tile["renderable"] is False
    assert tile["png_base64"] is None
    assert "Unsupported image data dimensions" in tile["render_error"]


def test_display_plane_rejects_empty_or_unsupported_arrays() -> None:
    with pytest.raises(ValueError, match="Unsupported image data dimensions"):
        _display_plane(np.ones((1, 1, 1, 1, 1)))

    with pytest.raises(ValueError, match="Cannot render empty image data"):
        _normalize_to_uint8(np.array([], dtype=np.float32))