#!/bin/bash

set -euo pipefail

mkdir -p build-conda
cd build-conda

echo 'Building mrd conda package using CMake...'

CMAKE_ARGS=(
    -GNinja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_CXX_STANDARD=20
    "-DCMAKE_INSTALL_PREFIX=${PREFIX}"
)
if [[ -n "${CONDA_BUILD_SYSROOT:-}" ]]; then
    CMAKE_ARGS+=("-DCMAKE_OSX_SYSROOT=${CONDA_BUILD_SYSROOT}")
fi

cmake "${CMAKE_ARGS[@]}" ../

ninja install
