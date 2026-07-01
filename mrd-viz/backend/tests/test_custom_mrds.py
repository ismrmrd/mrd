from __future__ import annotations

# Custom MRD tests fill only the gaps the generator does not expose directly.
# They stay intentionally small: a multi-plane image, thumbnail truncation, and
# a header-only file are enough to exercise the backend's edge classifications.

from pathlib import Path

import numpy as np

from mrd_viz.main import PreviewOptions, open_file

from helpers import write_header_only_mrd, write_image_mrd


def test_custom_multiplane_image_reports_shape_and_renders_first_plane(tmp_path: Path) -> None:
    path = tmp_path / "multiplane.mrd"
    write_image_mrd(path, [np.arange(2 * 3 * 5 * 6, dtype=np.float32).reshape(2, 3, 5, 6)])

    payload = open_file(path, PreviewOptions(max_thumbnails=1, thumbnail_size=4, read_full_stream=True))
    tile = payload["mosaic"]["thumbnails"][0]

    assert payload["file_class"] == "reconstructed"
    assert tile["renderable"] is True
    assert tile["data_shape"] == [2, 3, 5, 6]
    assert tile["source_plane"] == {"channel": 0, "z": 0}
    assert max(tile["rendered_shape"]) == 4


def test_custom_image_thumbnail_limit_marks_truncation(tmp_path: Path) -> None:
    path = tmp_path / "two_images.mrd"
    write_image_mrd(path, [np.ones((1, 1, 4, 4)), np.ones((1, 1, 4, 4)) * 2])

    payload = open_file(path, PreviewOptions(max_thumbnails=1, read_full_stream=True))

    assert payload["stream"]["image_count"] == 2
    assert len(payload["mosaic"]["thumbnails"]) == 1
    assert payload["mosaic"]["truncated"] is True
    assert payload["stream"]["partial"] is False


def test_custom_header_only_file_is_unknown(tmp_path: Path) -> None:
    path = tmp_path / "header_only.mrd"
    write_header_only_mrd(path)

    payload = open_file(path, PreviewOptions(read_full_stream=True))

    assert payload["ok"] is True
    assert payload["file_class"] == "unknown"
    assert payload["display_mode"] == "metadata_only"
    assert payload["warnings"] == ["No acquisition or image stream items were found."]