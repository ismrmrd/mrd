#!/usr/bin/env bash
# Test version-agnostic reading with mrd.dynamic.DynamicMrdReader against files
# written by DIFFERENT schema versions, all read back with the CURRENT library:
#
#   1. v2.2.0  - the released tag (old union tag CASING + fewer fields/variants),
#                generated with generate_v220.py, verified with verify_dynamic_read.py.
#   2. main    - the main branch's current schema (a distinct "2.2.1" schema that
#                differs from this branch: e.g. arrayComplexFloat vs
#                ndArrayComplexFloat). Generated with generate_stream.py.
#   3. current - this branch's own schema (control: schema matches, both readers
#                accept). Generated with generate_stream.py.
#
# Each old/foreign file must be REJECTED by the stock BinaryMrdReader (schema
# mismatch) yet read correctly by DynamicMrdReader.

set -euo pipefail

TESTDIR=$(dirname "$(realpath "$0")")
WORKSPACE=$(dirname "$(dirname "$TESTDIR")")

export PYTHONPATH="${WORKSPACE}/python:${PYTHONPATH:-}"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

build_module() {  # <git-ref> <dest-parent>   -> prints module dir
    local ref="$1" dest="$2"
    local mod="$dest/mrd"
    mkdir -p "$mod"
    git -C "$WORKSPACE" archive "$ref" python/mrd/ | tar -x --strip-components=2 -C "$mod"
    echo "$dest"
}

echo "== 1. v2.2.0 file =="
echo "  Building mrd v2.2.0 module from git tag ..."
V220_MODDIR=$(build_module v2.2.0 "$WORKDIR/mrd_v220")
V220="$WORKDIR/test_v220.mrd"
echo "  Generating v2.2.0 stream ..."
PYTHONPATH="$V220_MODDIR:${PYTHONPATH:-}" python3 "$TESTDIR/generate_v220.py" "$V220"
echo "  Reading with current DynamicMrdReader ..."
python3 "$TESTDIR/verify_dynamic_read.py" "$V220"

echo "== 2. main-branch file (current version, != 2.2.0) =="
echo "  Building mrd module from 'main' ..."
MAIN_MODDIR=$(build_module main "$WORKDIR/mrd_main")
MAINF="$WORKDIR/test_main.mrd"
echo "  Generating stream with main's schema ..."
PYTHONPATH="$MAIN_MODDIR:${PYTHONPATH:-}" python3 "$TESTDIR/generate_stream.py" "$MAINF"
echo "  Reading with current DynamicMrdReader ..."
python3 "$TESTDIR/verify_dynamic_stream.py" "$MAINF"

echo "== 3. current-branch file (control: schema matches) =="
CURF="$WORKDIR/test_current.mrd"
echo "  Generating stream with current schema ..."
python3 "$TESTDIR/generate_stream.py" "$CURF"
echo "  Reading with current DynamicMrdReader ..."
python3 "$TESTDIR/verify_dynamic_stream.py" "$CURF"

echo "Dynamic-read tests passed (v2.2.0, main, current)."
