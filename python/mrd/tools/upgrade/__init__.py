#!/usr/bin/env python3
"""Upgrade an MRD binary file from an older schema version to the current version."""

import argparse
import os
import sys
import tempfile
from collections.abc import Callable

import mrd
from mrd.binary import BinaryMrdWriter

from ._schema_registry import identify_file_version, KNOWN_SCHEMAS, _CURRENT_VERSION
from ._v220_reader import V220MrdReader

# ---------------------------------------------------------------------------
# Upgrade graph
#
# _SUPPORTED_UPGRADES maps each source version to the next version in the
# upgrade chain. upgrade_mrd_file follows the chain automatically, so a file
# two or more steps behind the current version is upgraded in a single call.
#
# To add support for a new version X.Y.Z → X.Y.Z+1:
#   1. Add "X.Y.Z": "X.Y.Z+1" to _SUPPORTED_UPGRADES.
#   2. Implement _upgrade_XYZ_to_XYZ1 and add it to _UPGRADE_FUNCTIONS.
# ---------------------------------------------------------------------------

_SUPPORTED_UPGRADES: dict[str, str] = {
    "2.2.0": "2.2.1",
}


def _upgrade_220_to_221(src: str, dst: str) -> None:
    with V220MrdReader(src) as reader:
        header = reader.read_header()
        with BinaryMrdWriter(dst) as writer:
            writer.write_header(header)
            writer.write_data(reader.read_data())


# Maps each source version to the function that performs one upgrade step.
_UPGRADE_FUNCTIONS: dict[str, Callable[[str, str], None]] = {
    "2.2.0": _upgrade_220_to_221,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upgrade_mrd_file(src: str, dst: str) -> None:
    """Upgrade an MRD binary file to the current schema version.

    Follows the upgrade chain automatically: if the source file is more than
    one version behind, intermediate steps are performed via temporary files
    that are cleaned up on completion.

    The upgrade is written to a temporary file in the same directory as *dst*
    and atomically renamed on success, so a failed upgrade never leaves *dst*
    in a partial state. *src* and *dst* may refer to the same path.

    Parameters
    ----------
    src:
        Path to the source MRD file.
    dst:
        Path to write the upgraded MRD file.
    """
    version = identify_file_version(src)
    if version is None:
        raise ValueError(
            f"{src!r}: unrecognised MRD schema version — cannot upgrade.\n"
            f"Known versions: {', '.join(sorted(KNOWN_SCHEMAS))}"
        )

    if version == _CURRENT_VERSION:
        raise ValueError(
            f"{src!r} is already at the current schema version ({_CURRENT_VERSION}) — "
            "no upgrade needed."
        )

    if version not in _SUPPORTED_UPGRADES:
        raise ValueError(
            f"{src!r}: upgrade from version {version!r} is not supported.\n"
            f"Supported source versions: {', '.join(sorted(_SUPPORTED_UPGRADES))}"
        )

    # Build the ordered list of upgrade steps from the source version to the
    # current version by following the chain in _SUPPORTED_UPGRADES.
    steps: list[str] = []
    v = version
    while v != _CURRENT_VERSION:
        if v not in _SUPPORTED_UPGRADES:
            raise ValueError(
                f"No complete upgrade path from {version!r} to {_CURRENT_VERSION!r}: "
                f"chain is broken at {v!r}."
            )
        steps.append(v)
        v = _SUPPORTED_UPGRADES[v]

    # Always stage the final output in a temp file next to dst, then atomically
    # rename it into place.  This ensures dst is never left in a partial state
    # if the upgrade raises mid-stream, and also makes src == dst safe.
    dst_dir = os.path.dirname(os.path.abspath(dst))
    if not os.path.isdir(dst_dir):
        raise FileNotFoundError(
            f"Destination directory does not exist: {dst_dir!r}"
        )
    fd, tmp_dst = tempfile.mkstemp(dir=dst_dir, suffix=".mrd.tmp")
    os.close(fd)
    try:
        if len(steps) == 1:
            _UPGRADE_FUNCTIONS[steps[0]](src, tmp_dst)
        else:
            # Multi-step path: chain through additional intermediate temp files.
            current_src = src
            tmp_intermediates: list[str] = []
            try:
                for i, step_version in enumerate(steps):
                    is_final = (i == len(steps) - 1)
                    if is_final:
                        step_dst = tmp_dst
                    else:
                        fd2, step_dst = tempfile.mkstemp(dir=dst_dir, suffix=".mrd.tmp")
                        os.close(fd2)
                        tmp_intermediates.append(step_dst)
                    _UPGRADE_FUNCTIONS[step_version](current_src, step_dst)
                    current_src = step_dst
            finally:
                for t in tmp_intermediates:
                    try:
                        os.unlink(t)
                    except OSError:
                        pass
        os.replace(tmp_dst, dst)
    except Exception:
        try:
            os.unlink(tmp_dst)
        except OSError:
            pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Upgrade an MRD binary file to the current schema version ({_CURRENT_VERSION}).",
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
        upgrade_mrd_file(src, src)
        print(f"Upgraded {src!r} in place.")
    else:
        dst = args.output if args.output else src + ".upgraded"
        upgrade_mrd_file(src, dst)
        print(f"Upgraded {src!r} → {dst!r}")
