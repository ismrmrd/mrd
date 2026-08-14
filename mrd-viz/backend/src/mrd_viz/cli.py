"""CLI entry point for the MRD Viz backend contract."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .html_harness import write_mosaic_html
from .main import DEFAULT_OPTIONS, PreviewOptions, classify_file, extract_image, open_file


def _package_version() -> str:
    try:
        return version("mrd-viz")
    except PackageNotFoundError:  # running from a source tree without install metadata
        return "unknown"


# _coords_from_pairs builds a dense tuple spanning up to the largest supplied axis, so an
# out-of-range AXIS (e.g. --slice 1000000000:0) would attempt an enormous allocation before
# any JSON error handling runs. MRD arrays are low-dimensional; cap AXIS well above that.
_MAX_SLICE_AXIS = 31


def _slice_pair(value: str) -> tuple[int, int]:
    axis_str, sep, index_str = value.partition(":")
    if not sep:
        raise argparse.ArgumentTypeError(f"--slice expects AXIS:INDEX, got {value!r}")
    try:
        axis = int(axis_str)
        index = int(index_str)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--slice expects integer AXIS:INDEX, got {value!r}") from exc
    if axis < 0 or index < 0:
        raise argparse.ArgumentTypeError(f"--slice AXIS and INDEX must be non-negative, got {value!r}")
    if axis > _MAX_SLICE_AXIS:
        raise argparse.ArgumentTypeError(f"--slice AXIS must be <= {_MAX_SLICE_AXIS}, got {value!r}")
    return axis, index


def _coords_from_pairs(pairs: list[tuple[int, int]] | None) -> tuple[int, ...]:
    if not pairs:
        return ()
    mapping = dict(pairs)
    return tuple(mapping.get(axis, 0) for axis in range(max(mapping) + 1))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mrd-viz")
    parser.add_argument("--version", action="version", version=f"mrd-viz {_package_version()}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser("classify", help="Return the stream classification for an MRD file")
    classify_parser.add_argument("path", type=Path)

    open_parser = subparsers.add_parser("open", aliases=["inspect"], help="Return the open-file payload")
    open_parser.add_argument("path", type=Path)
    open_parser.add_argument("--max-thumbnails", type=int, default=DEFAULT_OPTIONS.max_thumbnails)
    open_parser.add_argument("--thumbnail-size", type=int, default=DEFAULT_OPTIONS.thumbnail_size)
    open_parser.add_argument(
        "--explode-slices",
        dest="explode_slices",
        action="store_true",
        help="Emit one mosaic thumbnail per z slice instead of one per image",
    )

    image_parser = subparsers.add_parser("image", help="Return one full-resolution image payload by mosaic image index")
    image_parser.add_argument("path", type=Path)
    image_parser.add_argument("--index", type=int, required=True)
    image_parser.add_argument(
        "--slice",
        dest="slice",
        action="append",
        type=_slice_pair,
        metavar="AXIS:INDEX",
        help="Select a leading-axis slice index (repeatable, e.g. --slice 0:2 --slice 1:5)",
    )

    html_parser = subparsers.add_parser("html", help="Write a static HTML mosaic harness for one MRD file")
    html_parser.add_argument("path", type=Path)
    html_parser.add_argument("--output", type=Path, required=True)
    html_parser.add_argument("--max-thumbnails", type=int, default=DEFAULT_OPTIONS.max_thumbnails)
    html_parser.add_argument("--thumbnail-size", type=int, default=DEFAULT_OPTIONS.thumbnail_size)
    html_parser.add_argument("--preload-full-images", type=int, default=DEFAULT_OPTIONS.preload_full_images)

    return parser


def _emit_payload(payload: dict) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok", False) else 1


def _run_classify(path: Path) -> int:
    return _emit_payload(classify_file(path))


def _run_inspect(path: Path, max_thumbnails: int, thumbnail_size: int, explode_slices: bool) -> int:
    options = PreviewOptions(
        max_thumbnails=max_thumbnails,
        thumbnail_size=thumbnail_size,
        explode_slices=explode_slices,
    )
    return _emit_payload(open_file(path, options))


def _run_image(path: Path, index: int, slice_pairs: list[tuple[int, int]] | None) -> int:
    return _emit_payload(extract_image(path, index, _coords_from_pairs(slice_pairs)))


def _run_html(path: Path, output: Path, max_thumbnails: int, thumbnail_size: int, preload_full_images: int) -> int:
    preflight = open_file(path, PreviewOptions(max_thumbnails=0, thumbnail_size=thumbnail_size))
    if not preflight.get("ok", False):
        return _emit_payload(preflight)

    written_path = write_mosaic_html(
        path,
        output,
        max_thumbnails=max_thumbnails,
        thumbnail_size=thumbnail_size,
        preload_full_images=preload_full_images,
    )
    return _emit_payload({"ok": True, "output": str(written_path)})


def main(argv: list[str] | None = None) -> int:
    """Run the mrd-viz command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "classify":
        return _run_classify(args.path)
    if args.command in {"open", "inspect"}:
        return _run_inspect(args.path, args.max_thumbnails, args.thumbnail_size, args.explode_slices)
    if args.command == "image":
        return _run_image(args.path, args.index, args.slice)
    if args.command == "html":
        return _run_html(args.path, args.output, args.max_thumbnails, args.thumbnail_size, args.preload_full_images)

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())