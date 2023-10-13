#!/bin/bash
set -eo pipefail

# activate conda environment
source "/opt/conda/etc/profile.d/conda.sh"
conda activate mrd

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DEPENDENCIES_DIR="${THIS_DIR}/dependencies"
CURRENT_DIR="${PWD}"

rm -rf "${DEPENDENCIES_DIR}"
mkdir -p "${DEPENDENCIES_DIR}"
cd "${DEPENDENCIES_DIR}"

# Clone ISMRMRD
ISMRMRD_SHA1="595bd68d9138087f17ac792e972178af768dbab1"
git clone https://github.com/ismrmrd/ismrmrd.git
cd ismrmrd
git checkout "${ISMRMRD_SHA1}"

# Build ISMRMRD
mkdir -p build
cd build
cmake -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="${CONDA_PREFIX}" ..
ninja install

cd "${CURRENT_DIR}"
rm -rf "${DEPENDENCIES_DIR}"
