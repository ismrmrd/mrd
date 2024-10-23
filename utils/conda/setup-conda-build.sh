#!/usr/bin/env bash

set -e

# conda deactivate
conda install -y -n base conda-build anaconda-client
conda activate base
