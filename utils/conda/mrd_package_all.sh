#!/usr/bin/env bash

set -e

# conda deactivate
mamba install -n base conda-build conda-verify anaconda-client
conda activate base
pushd cpp/conda
../../utils/conda/package.sh
popd
pushd python/conda
../../utils/conda/package.sh
popd
