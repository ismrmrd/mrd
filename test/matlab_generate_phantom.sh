#!/usr/bin/env bash

set -e

suffix="$(shuf -er -n20  {A..Z} {a..z} {0..9} | tr -d '\n')"
tempname="phantom.${suffix}.bin"

function cleanup() {
    rm -f "${tempname}"
}
trap cleanup EXIT

cmd="generate_phantom(\"${tempname}\")"
# matlab -batch "${cmd}" >&2
run-matlab-command "${cmd}" >&2

cat "${tempname}"
