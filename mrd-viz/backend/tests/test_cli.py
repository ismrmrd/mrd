from __future__ import annotations

# CLI contract tests run the backend the same way the VS Code extension will:
# as a short-lived subprocess whose stdout is JSON. They verify both successful
# payloads and clean expected errors, including the new exit-code behavior.

import json
import os
import subprocess
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = BACKEND_ROOT / "src"


def run_cli(*args: object) -> tuple[subprocess.CompletedProcess[str], dict]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "mrd_viz.cli", *[str(arg) for arg in args]],
        cwd=BACKEND_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, json.loads(result.stdout)


def test_cli_open_classify_image_and_inspect_emit_json(generated_mrd_pair: tuple[Path, Path]) -> None:
    raw_path, recon_path = generated_mrd_pair

    open_result, open_payload = run_cli("open", recon_path, "--max-thumbnails", 1)
    classify_result, classify_payload = run_cli("classify", raw_path)
    image_result, image_payload = run_cli("image", recon_path, "--index", 0)
    inspect_result, inspect_payload = run_cli("inspect", recon_path, "--max-thumbnails", 1)

    assert open_result.returncode == 0
    assert open_payload["file_class"] == "reconstructed"
    assert open_payload["file_class_reliable"] is False
    assert open_payload["stream"]["partial"] is True
    assert classify_result.returncode == 0
    assert classify_payload["file_class"] == "raw"
    assert classify_payload["file_class_reliable"] is True
    assert image_result.returncode == 0
    assert image_payload["image"]["renderable"] is True
    assert inspect_result.returncode == 0
    assert inspect_payload["schema_version"] == open_payload["schema_version"]
    assert inspect_payload["file_class_reliable"] is False


def test_cli_html_writes_output_for_valid_mrd(generated_mrd_pair: tuple[Path, Path], tmp_path: Path) -> None:
    _, recon_path = generated_mrd_pair
    output_path = tmp_path / "preview.html"

    result, payload = run_cli("html", recon_path, "--output", output_path, "--max-thumbnails", 1)

    assert result.returncode == 0
    assert payload == {"ok": True, "output": str(output_path)}
    assert output_path.exists()


def test_cli_clean_file_errors_exit_one(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.mrd"
    output_path = tmp_path / "missing.html"

    for args in [("open", missing_path), ("classify", missing_path), ("html", missing_path, "--output", output_path)]:
        result, payload = run_cli(*args)
        assert result.returncode == 1
        assert payload["ok"] is False
        assert payload["file_class"] == "invalid"
        assert payload["file_class_reliable"] is True
        assert "File not found" in payload["error"]


def test_cli_clean_image_error_exits_one(generated_mrd_pair: tuple[Path, Path]) -> None:
    _, recon_path = generated_mrd_pair

    result, payload = run_cli("image", recon_path, "--index", 99)

    assert result.returncode == 1
    assert payload["ok"] is False
    assert "not found" in payload["error"]


def test_cli_image_accepts_slice_options(generated_mrd_pair: tuple[Path, Path]) -> None:
    _, recon_path = generated_mrd_pair

    result, payload = run_cli("image", recon_path, "--index", 0, "--slice", "0:0", "--slice", "1:0")

    assert result.returncode == 0
    assert payload["image"]["renderable"] is True
    assert "slice_dims" in payload["image"]
    assert isinstance(payload["image"]["source_plane"], dict)


def test_cli_image_rejects_malformed_slice(generated_mrd_pair: tuple[Path, Path]) -> None:
    _, recon_path = generated_mrd_pair

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "mrd_viz.cli", "image", str(recon_path), "--index", "0", "--slice", "bogus"],
        cwd=BACKEND_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "AXIS:INDEX" in result.stderr


def test_cli_open_explode_slices_emits_tiles(generated_mrd_pair: tuple[Path, Path]) -> None:
    _, recon_path = generated_mrd_pair

    default_result, default_payload = run_cli("open", recon_path, "--max-thumbnails", 64)
    exploded_result, exploded_payload = run_cli("open", recon_path, "--max-thumbnails", 64, "--explode-slices")

    assert default_result.returncode == 0
    assert exploded_result.returncode == 0
    default_tiles = default_payload["mosaic"]["thumbnails"]
    exploded_tiles = exploded_payload["mosaic"]["thumbnails"]
    assert len(exploded_tiles) >= len(default_tiles)

