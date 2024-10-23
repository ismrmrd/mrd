#!/bin/bash
set -euo pipefail

usage()
{
  cat << EOF

Builds the conda package in the current working directory.

Usage: $0
EOF
}

output_path="$(pwd)/build_pkg"

# Build up channel directives
channels=(
  conda-forge
  ismrmrd
)

channel_directives=$(printf -- "-c %s " "${channels[@]}")

mkdir -p "$output_path"
bash -c "conda build --no-anaconda-upload --output-folder $output_path $channel_directives $(pwd)"
