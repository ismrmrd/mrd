#!/usr/bin/env bash
# Test the mrd-upgrade tool end-to-end:
#   1. Build an isolated mrd v2.2.0 Python module from the git tag
#      (only the generated files differ; _binary.py is identical between versions)
#   2. Generate a v2.2.0 MRD stream (exercising most StreamItem variants)
#   3. Upgrade it to v2.2.1 with mrd-upgrade
#   4. Verify the output with the current mrd-python install

set -eo pipefail

TESTDIR=$(dirname "$(realpath "$0")")
WORKSPACE=$(dirname "$(dirname "$TESTDIR")")

export PYTHONPATH="${WORKSPACE}/python:${PYTHONPATH:-}"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "  Building mrd v2.2.0 module from git tag ..."
V220_MOD="$WORKDIR/mrd_v220/mrd"
mkdir -p "$V220_MOD"

# _binary.py and yardl_types.py are byte-for-byte identical between v2.2.0 and
# v2.2.1 (confirmed via git diff).  Copy them from the current workspace so the
# generator runs against the same codec as the upgrader.
cp "$WORKSPACE/python/mrd/_binary.py"    "$V220_MOD/"
cp "$WORKSPACE/python/mrd/yardl_types.py" "$V220_MOD/"

# Extract the v2.2.0 generated files (schema + type definitions) from git.
for f in __init__.py binary.py types.py protocols.py ndjson.py; do
    git -C "$WORKSPACE" show "v2.2.0:python/mrd/$f" > "$V220_MOD/$f"
done

echo "  Generating v2.2.0 stream ..."
V220="$WORKDIR/test_v220.mrd"
# Prepend the v2.2.0 module dir so it shadows the current mrd-python install.
PYTHONPATH="$WORKDIR/mrd_v220:${PYTHONPATH:-}" python3 "$TESTDIR/generate_v220.py" "$V220"

echo "  Verifying source file is detected as v2.2.0 ..."
detected=$(python3 - "$V220" <<'EOF'
import sys
from mrd.tools._schema_registry import identify_file_version
v = identify_file_version(sys.argv[1])
if v != "2.2.0":
    raise RuntimeError(f"Expected 2.2.0, got {v!r}")
print(v)
EOF
)
echo "    Detected: $detected"

echo "  Upgrading to v2.2.1 ..."
V221="$WORKDIR/test_v221.mrd"
mrd-upgrade "$V220" "$V221"

echo "  Verifying upgraded file ..."
python3 "$TESTDIR/verify_upgrade.py" "$V221"

echo "  Testing --in-place upgrade ..."
cp "$V220" "$WORKDIR/test_inplace.mrd"
mrd-upgrade --in-place "$WORKDIR/test_inplace.mrd"
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
