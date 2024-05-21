#!/usr/bin/env bash

set -e

# conda deactivate
mamba install -y -n base conda-build conda-verify anaconda-client boa
conda activate base
