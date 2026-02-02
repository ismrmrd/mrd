#!/bin/bash

set -euo pipefail

mkdir -p build-conda
cd build-conda

echo 'Building mrd conda package using CMake...'

cmake -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_STANDARD=20 \
    -DCMAKE_INSTALL_PREFIX=${PREFIX} \
    -DCMAKE_OSX_SYSROOT=${CONDA_BUILD_SYSROOT} \
    ../

ninja install
