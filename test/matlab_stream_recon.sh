#!/usr/bin/env bash

set -e

suffix="$(shuf -er -n20  {A..Z} {a..z} {0..9} | tr -d '\n')"

pipe_in="pipe.recon.${suffix}.in"
pipe_out="pipe.recon.${suffix}.out"

function cleanup() {
    rm -f "${pipe_in}" "${pipe_out}"
}
trap cleanup EXIT

mkfifo "${pipe_in}"
mkfifo "${pipe_out}"

# 1. Start output job
cat "${pipe_out}" &

# 2. Start MATLAB job
cmd="stream_recon(\"${pipe_in}\", \"${pipe_out}\")"
# matlab -batch "${cmd}" >&2 &
run-matlab-command "${cmd}" >&2 &

# 3. Start input job
cat /dev/stdin > "${pipe_in}"

wait
