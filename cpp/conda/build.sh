#!/bin/bash

set -euo pipefail

mkdir -p build-conda
cd build-conda

if [[ $(uname) == Darwin ]]; then
    export CFLAGS="${CFLAGS:-} -isysroot ${CONDA_BUILD_SYSROOT} -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET}"
    export CXXFLAGS="${CXXFLAGS:-} -isysroot ${CONDA_BUILD_SYSROOT} -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET}"
#     export SDKROOT="${CONDA_BUILD_SYSROOT}"
fi

echo 'Building mrd conda package using CMake...'

cmake -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${PREFIX} \
      ../

ninja install
