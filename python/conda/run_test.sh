#!/usr/bin/env bash

set -euo pipefail

python -m mrd.tools.minimal_example

python -m mrd.tools.phantom | python -m mrd.tools.stream_recon | python -m mrd.tools.export_png_images
