#!/usr/bin/env bash

set -euo pipefail

python -m mrd.tools.phantom | python -m mrd.tools.stream_recon | python -m mrd.tools.image_stream_to_png
