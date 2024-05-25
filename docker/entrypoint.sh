#!/bin/bash

set -eo pipefail

# Enable conda for this shell
. /opt/conda/etc/profile.d/conda.sh

# Activate the environment
conda activate mrd

exec "$@"
