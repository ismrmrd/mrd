from __future__ import annotations

# Generated MRD tests use the real phantom and stream reconstruction tools to
# cover realistic raw and reconstructed files. This gives broad end-to-end
# confidence while keeping fixtures reproducible and small enough for CI.

from pathlib import Path

from mrd.tools.phantom import generate_cartesian_phantom

from mrd_viz.main import PreviewOptions, open_file


def test_generated_raw_phantom_is_metadata_only(generated_mrd_pair: tuple[Path, Path]) -> None:
    raw_path, _ = generated_mrd_pair

    payload = open_file(raw_path, PreviewOptions(read_full_stream=True))

    assert payload["ok"] is True
    assert payload["file_class"] == "raw"
    assert payload["display_mode"] == "metadata_only"
    assert payload["stream"]["acquisition_count"] > 0
    assert payload["stream"]["image_count"] == 0
    assert payload["metadata"]["acquisitions"][0]["data_shape"] == [4, 32]
    assert payload["warnings"] == ["Raw-only MRD files are summarized but not visualized."]


def test_generated_recon_phantom_renders_mosaic(generated_mrd_pair: tuple[Path, Path]) -> None:
    _, recon_path = generated_mrd_pair

    payload = open_file(recon_path, PreviewOptions(max_thumbnails=4, thumbnail_size=8, read_full_stream=True))

    first_tile = payload["mosaic"]["thumbnails"][0]

    assert payload["ok"] is True
    assert payload["file_class"] == "reconstructed"
    assert payload["display_mode"] == "mosaic"
    assert payload["stream"]["image_count"] == 2
    assert first_tile["renderable"] is True
    assert first_tile["data_shape"] == [1, 1, 16, 16]
    assert first_tile["rendered_shape"] == [8, 8]


def test_generated_featureful_raw_phantom_summarizes_multicoil_acquisitions(tmp_path: Path) -> None:
    raw_path = tmp_path / "featureful_raw.mrd"
    generate_cartesian_phantom(
        str(raw_path),
        ncoils=3,
        matrix_size=12,
        repetitions=2,
        acceleration=2,
        oversampling=2,
        calibration_width=4,
        noise_calibration=True,
        store_coordinates=True,
        noise_level=0.0,
    )

    payload = open_file(raw_path, PreviewOptions(read_full_stream=True, max_acquisition_examples=4))

    assert payload["ok"] is True
    assert payload["file_class"] == "raw"
    assert payload["summary"]["encoded_matrix"] == [24, 12, 1]
    assert payload["stream"]["acquisition_count"] > 32
    assert payload["metadata"]["acquisitions"][0]["data_shape"] == [3, 24]