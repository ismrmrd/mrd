#!/bin/bash

set -euo pipefail

# Smoketest A
mrd_phantom -o mrd_testdata.h5
mrd_hdf5_to_stream mrd_testdata.h5 | mrd_stream_recon | mrd_stream_to_hdf5 mrd_testdata_recon.h5

# Smoketest B
mrd_phantom -s | mrd_to_ismrmrd | ismrmrd_to_mrd | mrd_stream_recon | mrd_image_stream_to_png
