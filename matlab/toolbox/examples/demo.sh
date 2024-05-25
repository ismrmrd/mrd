#!/usr/bin/env bash

# A simple demonstration of how to use named pipes to stream data to
# and from the MATLAB example tools

mkfifo phantom_in
mkfifo images_out

function cleanup() {
    rm -f phantom_in images_out
}
trap cleanup EXIT

export MATLABPATH=../

matlab -batch 'export_png_images("images_out");' &
matlab -batch 'stream_recon("phantom_in", "images_out");' &
matlab -batch 'generate_phantom("phantom_in", repetitions=3);'
