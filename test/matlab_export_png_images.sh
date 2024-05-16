#!/usr/bin/env bash

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_prefix>"
    exit 1
fi

suffix="$(shuf -er -n20  {A..Z} {a..z} {0..9} | tr -d '\n')"
pipe="pipe.export.${suffix}"

function cleanup() {
    rm -f "${pipe}"
}
trap cleanup EXIT

mkfifo "${pipe}"

cmd="export_png_images(\"${pipe}\", output_prefix=\"${1}\")"
# matlab -batch "${cmd}" &
run-matlab-command "${cmd}" &

cat /dev/stdin > "${pipe}"

wait
