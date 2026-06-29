"""Stage 1 backend contract for the MRD Viewer extension.

The extension should call this module through the ``mrd-viz`` CLI. Stage 1 is
intentionally small: classify the stream, summarize the file, build thumbnail
tiles for reconstructed MRD image items, and return one full-resolution image
on demand.
"""

from __future__ import annotations

import base64
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from pathlib import Path
from typing import Any

import mrd
import numpy as np
from PIL import Image


class MrdFileClass(StrEnum):
    """High-level stream categories used by the Stage 1 UI."""

    RAW = "raw"
    RECONSTRUCTED = "reconstructed"
    MIXED = "mixed"
    UNKNOWN = "unknown"
    INVALID = "invalid"


class DisplayMode(StrEnum):
    """Rendering mode the extension should use for a file."""

    MOSAIC = "mosaic"
    METADATA_ONLY = "metadata_only"
    ERROR = "error"


@dataclass(slots=True)
class Stage1Options:
    """Controls for the initial file payload."""

    max_thumbnails: int = 512
    thumbnail_size: int = 192
    max_acquisition_examples: int = 8


def inspect_file(path: Path, options: Stage1Options | None = None) -> dict[str, Any]:
    """Return the Stage 1 payload for opening one MRD file.

    The payload is designed for the VS Code extension, but it is plain JSON so
    the CLI can also be used as a regression and debugging surface.
    """

    options = options or Stage1Options()
    path = Path(path)
    if not path.exists():
        return _error_payload(path, f"File not found: {path}")

    try:
        with mrd.BinaryMrdReader(str(path)) as reader:
            header = reader.read_header()
            if header is None:
                return _error_payload(path, "Missing MRD header")

            state = _new_state(path, header)
            for stream_index, item in enumerate(reader.read_data()):
                _consume_stream_item(state, item, stream_index, options)

            _finalize_state(state, options)
            return state
    except Exception as exc:
        return _error_payload(path, str(exc))


def extract_image(path: Path, image_index: int) -> dict[str, Any]:
    """Return one full-resolution image payload for lazy tile expansion."""

    path = Path(path)
    if not path.exists():
        return _error_payload(path, f"File not found: {path}")
    if image_index < 0:
        return _error_payload(path, "Image index must be non-negative")
    try:
        seen_images = 0
        selected_image: dict[str, Any] | None = None
        with mrd.BinaryMrdReader(str(path)) as reader:
            header = reader.read_header()
            if header is None:
                return _error_payload(path, "Missing MRD header")

            for stream_index, item in enumerate(reader.read_data()):
                image = _image_value(item)
                if image is None:
                    continue
                if seen_images == image_index and selected_image is None:
                    selected_image = _image_payload(image, _stream_item_type_name(item), stream_index, seen_images, thumbnail=False)
                seen_images += 1

        if selected_image is not None:
            return {
                "ok": True,
                "path": str(path),
                "image": selected_image,
            }
    except Exception as exc:
        return _error_payload(path, str(exc))

    return _error_payload(path, f"Image index {image_index} not found")


def classify_file(path: Path) -> dict[str, Any]:
    """Return only the classification subset of the Stage 1 payload."""

    payload = inspect_file(path, Stage1Options(max_thumbnails=0))
    return {
        "ok": payload["ok"],
        "path": payload["path"],
        "file_class": payload["file_class"],
        "display_mode": payload["display_mode"],
        "item_counts": payload["stream"]["item_counts"],
        "warnings": payload["warnings"],
        "error": payload.get("error"),
    }


def _new_state(path: Path, header: mrd.Header) -> dict[str, Any]:
    return {
        "ok": True,
        "schema_version": 1,
        "path": str(path),
        "filename": path.name,
        "file_size_bytes": path.stat().st_size,
        "file_class": MrdFileClass.UNKNOWN.value,
        "display_mode": DisplayMode.METADATA_ONLY.value,
        "summary": _header_summary(header),
        "stream": {
            "item_counts": {},
            "image_count": 0,
            "acquisition_count": 0,
            "waveform_count": 0,
            "other_count": 0,
        },
        "mosaic": {
            "tile_unit": "mrd_image_item",
            "thumbnails": [],
            "truncated": False,
        },
        "metadata": {
            "images": [],
            "acquisitions": [],
            "waveforms": [],
            "other_items": [],
        },
        "warnings": [],
    }


def _consume_stream_item(state: dict[str, Any], item: Any, stream_index: int, options: Stage1Options) -> None:
    item_type = _stream_item_type_name(item)
    item_counts: dict[str, int] = state["stream"]["item_counts"]
    item_counts[item_type] = int(item_counts.get(item_type, 0)) + 1

    image = _image_value(item)
    if image is not None:
        image_index = state["stream"]["image_count"]
        state["stream"]["image_count"] += 1
        state["metadata"]["images"].append(_image_metadata(image, item_type, stream_index, image_index))
        if image_index < options.max_thumbnails:
            state["mosaic"]["thumbnails"].append(_image_tile(image, item_type, stream_index, image_index, options))
        else:
            state["mosaic"]["truncated"] = True
        return

    acquisition = _acquisition_value(item)
    if acquisition is not None:
        state["stream"]["acquisition_count"] += 1
        if len(state["metadata"]["acquisitions"]) < options.max_acquisition_examples:
            state["metadata"]["acquisitions"].append(_acquisition_metadata(acquisition, stream_index))
        return

    waveform = _waveform_value(item)
    if waveform is not None:
        state["stream"]["waveform_count"] += 1
        state["metadata"]["waveforms"].append({"stream_index": stream_index, "type": item_type})
        return

    state["stream"]["other_count"] += 1
    state["metadata"]["other_items"].append({"stream_index": stream_index, "type": item_type})


def _finalize_state(state: dict[str, Any], options: Stage1Options) -> None:
    image_count = state["stream"]["image_count"]
    acquisition_count = state["stream"]["acquisition_count"]

    if image_count and acquisition_count:
        state["file_class"] = MrdFileClass.MIXED.value
        state["display_mode"] = DisplayMode.MOSAIC.value
        state["warnings"].append("Mixed MRD file: showing image mosaic and summarizing acquisitions.")
    elif image_count:
        state["file_class"] = MrdFileClass.RECONSTRUCTED.value
        state["display_mode"] = DisplayMode.MOSAIC.value
    elif acquisition_count:
        state["file_class"] = MrdFileClass.RAW.value
        state["display_mode"] = DisplayMode.METADATA_ONLY.value
        state["warnings"].append("Raw-only MRD files are summarized in Stage 1 but not visualized.")
    else:
        state["file_class"] = MrdFileClass.UNKNOWN.value
        state["display_mode"] = DisplayMode.METADATA_ONLY.value
        state["warnings"].append("No acquisition or image stream items were found.")

    if state["mosaic"]["truncated"] and options.max_thumbnails > 0:
        state["warnings"].append(f"Showing first {options.max_thumbnails} thumbnails; load individual images on demand.")


def _image_payload(
    image: mrd.Image,
    item_type: str,
    stream_index: int,
    image_index: int,
    *,
    thumbnail: bool,
    max_size: int = 192,
) -> dict[str, Any]:
    plane = _display_plane(np.asarray(image.data))
    png_base64, rendered_shape = _plane_to_png_base64(plane, thumbnail=thumbnail, max_size=max_size)
    payload = _image_metadata(image, item_type, stream_index, image_index)
    payload.update(
        {
            "png_base64": png_base64,
            "rendered_shape": rendered_shape,
            "thumbnail": thumbnail,
            "renderable": True,
            "render_error": None,
            "source_plane": {"channel": 0, "z": 0},
        }
    )
    return payload


def _image_tile(image: mrd.Image, item_type: str, stream_index: int, image_index: int, options: Stage1Options) -> dict[str, Any]:
    try:
        return _image_payload(image, item_type, stream_index, image_index, thumbnail=True, max_size=options.thumbnail_size)
    except Exception as exc:
        payload = _image_metadata(image, item_type, stream_index, image_index)
        payload.update(
            {
                "png_base64": None,
                "rendered_shape": None,
                "thumbnail": True,
                "renderable": False,
                "render_error": str(exc),
                "source_plane": None,
            }
        )
        return payload


def _display_plane(data: np.ndarray) -> np.ndarray:
    if data.ndim == 4:
        return data[0, 0, :, :]
    if data.ndim == 3:
        return data[0, :, :]
    if data.ndim == 2:
        return data
    raise ValueError(f"Unsupported image data dimensions: {list(data.shape)}")


def _plane_to_png_base64(plane: np.ndarray, *, thumbnail: bool, max_size: int) -> tuple[str, list[int]]:
    pixels = _normalize_to_uint8(plane)
    image = Image.fromarray(pixels, mode="L")
    if thumbnail:
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        image.thumbnail((max_size, max_size), resampling)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii"), [image.height, image.width]


def _normalize_to_uint8(array: np.ndarray) -> np.ndarray:
    values = np.asarray(array)
    if values.size == 0:
        raise ValueError("Cannot render empty image data")
    if np.iscomplexobj(values):
        values = np.abs(values)
    values = np.nan_to_num(values.astype(np.float32), copy=False)
    minimum = float(values.min())
    maximum = float(values.max())
    if maximum == minimum:
        return np.zeros(values.shape, dtype=np.uint8)
    scaled = (values - minimum) / (maximum - minimum)
    return np.clip(scaled * 255.0, 0, 255).astype(np.uint8)


def _header_summary(header: mrd.Header) -> dict[str, Any]:
    result: dict[str, Any] = {"encoding_count": len(getattr(header, "encoding", []) or [])}
    if not header.encoding:
        return result

    encoding = header.encoding[0]
    result.update(
        {
            "encoded_matrix": _matrix(getattr(encoding, "encoded_space", None)),
            "recon_matrix": _matrix(getattr(encoding, "recon_space", None)),
            "encoded_fov_mm": _field_of_view(getattr(encoding, "encoded_space", None)),
            "recon_fov_mm": _field_of_view(getattr(encoding, "recon_space", None)),
        }
    )
    return result


def _matrix(space: Any) -> list[int] | None:
    matrix_size = getattr(space, "matrix_size", None)
    if matrix_size is None:
        return None
    return [_safe_int(getattr(matrix_size, axis, None)) for axis in ("x", "y", "z")]


def _field_of_view(space: Any) -> list[float] | None:
    field_of_view = getattr(space, "field_of_view_mm", None)
    if field_of_view is None:
        return None
    return [_safe_float(getattr(field_of_view, axis, None)) for axis in ("x", "y", "z")]


def _image_metadata(image: mrd.Image, item_type: str, stream_index: int, image_index: int) -> dict[str, Any]:
    data = np.asarray(image.data)
    head = image.head
    return {
        "image_index": image_index,
        "stream_index": stream_index,
        "stream_item_type": item_type,
        "data_shape": list(data.shape),
        "dtype": str(data.dtype),
        "head": {
            "image_type": _safe_int(getattr(head, "image_type", None)),
            "image_series_index": _safe_int(getattr(head, "image_series_index", None)),
            "slice": _safe_int(getattr(head, "slice", None)),
            "phase": _safe_int(getattr(head, "phase", None)),
            "contrast": _safe_int(getattr(head, "contrast", None)),
            "repetition": _safe_int(getattr(head, "repetition", None)),
            "field_of_view": _safe_float_list(getattr(head, "field_of_view", None)),
        },
    }


def _acquisition_metadata(acquisition: mrd.Acquisition, stream_index: int) -> dict[str, Any]:
    head = acquisition.head
    return {
        "stream_index": stream_index,
        "data_shape": list(np.asarray(acquisition.data).shape),
        "dtype": str(np.asarray(acquisition.data).dtype),
        "flags": _safe_int(getattr(head, "flags", None)),
        "scan_counter": _safe_int(getattr(head, "scan_counter", None)),
        "idx": {
            "slice": _safe_int(getattr(head.idx, "slice", None)),
            "phase": _safe_int(getattr(head.idx, "phase", None)),
            "contrast": _safe_int(getattr(head.idx, "contrast", None)),
            "repetition": _safe_int(getattr(head.idx, "repetition", None)),
            "kspace_encode_step_1": _safe_int(getattr(head.idx, "kspace_encode_step_1", None)),
            "kspace_encode_step_2": _safe_int(getattr(head.idx, "kspace_encode_step_2", None)),
        },
    }


def _stream_item_type_name(item: Any) -> str:
    return type(item).__name__.replace("StreamItem.", "")


def _image_value(item: Any) -> mrd.Image | None:
    value = getattr(item, "value", None)
    return value if isinstance(value, mrd.Image) else None


def _acquisition_value(item: Any) -> mrd.Acquisition | None:
    value = getattr(item, "value", None)
    return value if isinstance(value, mrd.Acquisition) else None


def _waveform_value(item: Any) -> mrd.Waveform | None:
    value = getattr(item, "value", None)
    return value if isinstance(value, mrd.Waveform) else None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    raw_value = getattr(value, "value", value)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    raw_value = getattr(value, "value", value)
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _safe_float_list(value: Any) -> list[float] | None:
    if value is None:
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _error_payload(path: Path, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "schema_version": 1,
        "path": str(path),
        "filename": path.name,
        "file_size_bytes": path.stat().st_size if path.exists() else None,
        "file_class": MrdFileClass.INVALID.value,
        "display_mode": DisplayMode.ERROR.value,
        "summary": {},
        "stream": {"item_counts": {}, "image_count": 0, "acquisition_count": 0, "waveform_count": 0, "other_count": 0},
        "mosaic": {"tile_unit": "mrd_image_item", "thumbnails": [], "truncated": False},
        "metadata": {"images": [], "acquisitions": [], "waveforms": [], "other_items": []},
        "warnings": [],
        "error": message,
    }