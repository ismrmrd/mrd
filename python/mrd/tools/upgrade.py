#!/usr/bin/env python3
"""Upgrade an MRD binary file from an older schema version to the current version."""

import argparse
import os
import sys
import tempfile

import mrd
from mrd.binary import BinaryMrdWriter

from ._schema_registry import identify_file_version, KNOWN_SCHEMAS
from ._v220_reader import V220MrdReader

_SUPPORTED_UPGRADES: dict[str, str] = {
    "2.2.0": "2.2.1",
}


def upgrade_mrd_file(src: str, dst: str) -> None:
    """Upgrade an MRD binary file from its detected schema version to v2.2.1.

    Parameters
    ----------
    src:
        Path to the source MRD file.
    dst:
        Path to write the upgraded MRD file. Must differ from *src*.
    """
    version = identify_file_version(src)
    if version is None:
        raise ValueError(
            f"{src!r}: unrecognised MRD schema version — cannot upgrade.\n"
            f"Known versions: {', '.join(sorted(KNOWN_SCHEMAS))}"
        )

    if version == "2.2.1":
        raise ValueError(f"{src!r} is already at schema version 2.2.1 — no upgrade needed.")

    if version not in _SUPPORTED_UPGRADES:
        raise ValueError(
            f"{src!r}: upgrade from version {version!r} is not supported.\n"
            f"Supported source versions: {', '.join(sorted(_SUPPORTED_UPGRADES))}"
        )

    if version == "2.2.0":
        _upgrade_220_to_221(src, dst)
    else:
        raise AssertionError(f"Unhandled version {version!r}")


def _upgrade_220_to_221(src: str, dst: str) -> None:
    with V220MrdReader(src) as reader:
        header = reader.read_header()
        with BinaryMrdWriter(dst) as writer:
            writer.write_header(header)
            writer.write_data(reader.read_data())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upgrade an MRD binary file to the current schema version (v2.2.1).",
    )
    parser.add_argument("input", help="Source MRD binary file to upgrade.")
    parser.add_argument("output", nargs="?", help="Destination file (default: <input>.upgraded).")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Replace the source file with the upgraded version.",
    )
    args = parser.parse_args()

    src = args.input
    if not os.path.isfile(src):
        print(f"error: {src!r} does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.in_place:
        if args.output:
            parser.error("Cannot specify both an output file and --in-place.")
        # Write to a temp file next to the source, then atomically replace.
        src_dir = os.path.dirname(os.path.abspath(src))
        fd, tmp_path = tempfile.mkstemp(dir=src_dir, suffix=".tmp")
        os.close(fd)
        try:
            upgrade_mrd_file(src, tmp_path)
            os.replace(tmp_path, src)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        print(f"Upgraded {src!r} in place.")
    else:
        dst = args.output if args.output else src + ".upgraded"
        upgrade_mrd_file(src, dst)
        print(f"Upgraded {src!r} → {dst!r}")


if __name__ == "__main__":
    main()
