#!/usr/bin/env bash
# Test the mrd-upgrade tool end-to-end:
#   1. Extract the entire python/mrd/ tree from the v2.2.0 git tag via git archive
#      into a temp directory; prepend it to PYTHONPATH to shadow the installed package.
#   2. Generate a v2.2.0 MRD stream (exercising most StreamItem variants)
#   3. Upgrade it to v2.2.1 with mrd-upgrade
#   4. Verify the output with the current mrd-python install

set -euo pipefail

TESTDIR=$(dirname "$(realpath "$0")")
WORKSPACE=$(dirname "$(dirname "$TESTDIR")")

export PYTHONPATH="${WORKSPACE}/python:${PYTHONPATH:-}"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "  Building mrd v2.2.0 module from git tag ..."
V220_MOD="$WORKDIR/mrd_v220/mrd"
mkdir -p "$V220_MOD"

# Extract all v2.2.0 files from git.
git -C "$WORKSPACE" archive v2.2.0 python/mrd/ | tar -x --strip-components=2 -C "$V220_MOD"

echo "  Generating v2.2.0 stream ..."
V220="$WORKDIR/test_v220.mrd"
# Prepend the v2.2.0 module dir so it shadows the current mrd-python install.
PYTHONPATH="$WORKDIR/mrd_v220:${PYTHONPATH:-}" python3 "$TESTDIR/generate_v220.py" "$V220"

echo "  Verifying source file is detected as v2.2.0 ..."
detected=$(python3 - "$V220" <<'EOF'
import sys
from mrd.tools.upgrade import identify_file_version
v = identify_file_version(sys.argv[1])
if v != "2.2.0":
    raise RuntimeError(f"Expected 2.2.0, got {v!r}")
print(v)
EOF
)
echo "    Detected: $detected"

echo "  Upgrading to v2.2.1 ..."
V221="$WORKDIR/test_v221.mrd"
python3 -m mrd.tools.upgrade "$V220" "$V221"

echo "  Verifying upgraded file ..."
python3 "$TESTDIR/verify_upgrade.py" "$V221"

echo "  Testing --in-place upgrade ..."
cp "$V220" "$WORKDIR/test_inplace.mrd"
python3 -m mrd.tools.upgrade --in-place "$WORKDIR/test_inplace.mrd"
python3 "$TESTDIR/verify_upgrade.py" "$WORKDIR/test_inplace.mrd"

echo "  Testing error cases ..."
python3 - "$V221" <<'EOF'
import sys
from mrd.tools.upgrade import upgrade_mrd_file
try:
    upgrade_mrd_file(sys.argv[1], sys.argv[1] + ".should_not_exist")
    raise RuntimeError("Expected ValueError for already-current file")
except ValueError:
    pass  # expected
EOF

echo "Upgrade tests passed."
