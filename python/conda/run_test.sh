#!/usr/bin/env bash

set -euo pipefail

python -m mrd.tools.minimal_example

python -m mrd.tools.phantom \
    | python -m mrd.tools.mrd_to_ismrmrd \
    | python -m mrd.tools.ismrmrd_to_mrd \
    | python -m mrd.tools.stream_recon \
    | python -m mrd.tools.mrd_to_ismrmrd \
    | python -m mrd.tools.ismrmrd_to_mrd \
    | python -m mrd.tools.export_png_images \
