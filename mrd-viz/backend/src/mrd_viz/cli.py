"""CLI entry point for the Stage 1 MRD Viewer backend contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .html_harness import write_mosaic_html
from .stage1 import Stage1Options, classify_file, extract_image, inspect_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mrd-viz")
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser("classify", help="Return the stream classification for an MRD file")
    classify_parser.add_argument("path", type=Path)

    open_parser = subparsers.add_parser("open", aliases=["inspect"], help="Return the Stage 1 open-file payload")
    open_parser.add_argument("path", type=Path)
    open_parser.add_argument("--max-thumbnails", type=int, default=128)
    open_parser.add_argument("--thumbnail-size", type=int, default=192)

    image_parser = subparsers.add_parser("image", help="Return one full-resolution image payload by mosaic image index")
    image_parser.add_argument("path", type=Path)
    image_parser.add_argument("--index", type=int, required=True)

    html_parser = subparsers.add_parser("html", help="Write a static HTML mosaic harness for one MRD file")
    html_parser.add_argument("path", type=Path)
    html_parser.add_argument("--output", type=Path, required=True)
    html_parser.add_argument("--max-thumbnails", type=int, default=128)
    html_parser.add_argument("--thumbnail-size", type=int, default=128)
    html_parser.add_argument("--preload-full-images", type=int, default=1)

    return parser


def _run_classify(path: Path) -> int:
    print(json.dumps(classify_file(path), indent=2, sort_keys=True))
    return 0


def _run_inspect(path: Path, max_thumbnails: int, thumbnail_size: int) -> int:
    options = Stage1Options(max_thumbnails=max_thumbnails, thumbnail_size=thumbnail_size)
    print(json.dumps(inspect_file(path, options), indent=2, sort_keys=True))
    return 0


def _run_image(path: Path, index: int) -> int:
    print(json.dumps(extract_image(path, index), indent=2, sort_keys=True))
    return 0


def _run_html(path: Path, output: Path, max_thumbnails: int, thumbnail_size: int, preload_full_images: int) -> int:
    written_path = write_mosaic_html(
        path,
        output,
        max_thumbnails=max_thumbnails,
        thumbnail_size=thumbnail_size,
        preload_full_images=preload_full_images,
    )
    print(json.dumps({"ok": True, "output": str(written_path)}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the mrd-viz command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "classify":
        return _run_classify(args.path)
    if args.command in {"open", "inspect"}:
        return _run_inspect(args.path, args.max_thumbnails, args.thumbnail_size)
    if args.command == "image":
        return _run_image(args.path, args.index)
    if args.command == "html":
        return _run_html(args.path, args.output, args.max_thumbnails, args.thumbnail_size, args.preload_full_images)

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())