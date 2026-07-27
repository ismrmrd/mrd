from __future__ import annotations

# Synthetic array tests are the fastest guardrail for rendering semantics. They
# keep normalization, representative-plane selection, and unsupported-shape
# behavior pinned without paying the cost or fragility of writing MRD files.

import mrd
import numpy as np
import pytest

from mrd_viz.main import (
    PreviewOptions,
    _display_plane,
    _image_mosaic_tiles,
    _image_tile,
    _normalize_to_uint8,
    _plane_to_png_base64,
    _slice_dims,
)


def test_display_plane_selects_representative_plane() -> None:
    assert _display_plane(np.ones((3, 4))).shape == (3, 4)
    assert _display_plane(np.ones((2, 3, 4))).shape == (3, 4)
    assert _display_plane(np.ones((5, 2, 3, 4))).shape == (3, 4)


def test_display_plane_honors_and_clamps_slice_coords() -> None:
    data = np.arange(2 * 3 * 2 * 2, dtype=np.float32).reshape(2, 3, 2, 2)
    assert np.array_equal(_display_plane(data, [1, 2]), data[1, 2])
    # Missing trailing coords default to axis 0.
    assert np.array_equal(_display_plane(data, [1]), data[1, 0])
    # Out-of-range coords clamp to the last valid index on each axis.
    assert np.array_equal(_display_plane(data, [9, 9]), data[1, 2])
    # 3D data exposes a single leading (z) axis.
    data3 = np.arange(3 * 2 * 2, dtype=np.float32).reshape(3, 2, 2)
    assert np.array_equal(_display_plane(data3, [2]), data3[2])


def test_slice_dims_describes_leading_axes() -> None:
    assert _slice_dims((3, 4)) == []
    assert _slice_dims((5, 3, 4)) == [{"axis": 0, "name": "z", "size": 5}]
    assert _slice_dims((2, 5, 3, 4)) == [
        {"axis": 0, "name": "channel", "size": 2},
        {"axis": 1, "name": "z", "size": 5},
    ]
    # Shapes outside the canonical 3D/4D image layout expose no steppable axes.
    assert _slice_dims((1, 1, 1, 3, 4)) == []


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


def test_image_tile_renders_requested_slice() -> None:
    data = np.zeros((1, 2, 2, 2), dtype=np.float32)
    data[0, 1] = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32)
    image = mrd.Image[np.float32](
        head=mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE),
        data=data,
    )

    tile = _image_tile(
        image,
        "ImageFloat",
        stream_index=0,
        image_index=0,
        options=PreviewOptions(max_thumbnails=1),
        slice_coords=(0, 1),
    )

    assert tile["renderable"] is True
    assert tile["source_plane"] == {"channel": 0, "z": 1}
    assert tile["slice_dims"] == [
        {"axis": 0, "name": "channel", "size": 1},
        {"axis": 1, "name": "z", "size": 2},
    ]


def test_image_mosaic_tiles_explodes_z_slices() -> None:
    data = np.arange(1 * 3 * 2 * 2, dtype=np.float32).reshape(1, 3, 2, 2)
    image = mrd.Image[np.float32](
        head=mrd.ImageHeader(image_type=mrd.ImageType.MAGNITUDE),
        data=data,
    )

    # Without explode mode a single volume yields one tile.
    single, hit_limit = _image_mosaic_tiles(image, "ImageFloat", 0, 4, PreviewOptions(), limit=16)
    assert len(single) == 1
    assert hit_limit is False
    assert "tile_title" not in single[0]

    # Explode mode yields one tile per z slice, labeled and tagged with source_plane.
    exploded, hit_limit = _image_mosaic_tiles(image, "ImageFloat", 0, 4, PreviewOptions(explode_slices=True), limit=16)
    assert len(exploded) == 3
    assert hit_limit is False
    assert [tile["source_plane"]["z"] for tile in exploded] == [0, 1, 2]
    assert exploded[2]["tile_title"] == "Image 4 \u00b7 z 2"

    # The per-image limit truncates the exploded tiles.
    limited, hit_limit = _image_mosaic_tiles(image, "ImageFloat", 0, 4, PreviewOptions(explode_slices=True), limit=2)
    assert len(limited) == 2
    assert hit_limit is True


def test_display_plane_rejects_empty_or_unsupported_arrays() -> None:
    with pytest.raises(ValueError, match="Unsupported image data dimensions"):
        _display_plane(np.ones((1, 1, 1, 1, 1)))

    with pytest.raises(ValueError, match="Cannot render empty image data"):
        _normalize_to_uint8(np.array([], dtype=np.float32))