#!/usr/bin/env bash

set -eo pipefail

# If this is run from within a devcontainer, we need to bind mount the HOST's workspace directory
if [ -n "${HOST_WORKSPACE_DIR:-}" ]; then
    WRITEDIR="${HOST_WORKSPACE_DIR:-}"
else
    WRITEDIR="$(pwd)"
fi

if [ -n "${CONTAINER_WORKSPACE_DIR:-}" ]; then
    READDIR="${CONTAINER_WORKSPACE_DIR:-}"
else
    READDIR="$(pwd)"
fi

rm -f "${READDIR}/*.png"

docker run --rm -i ghcr.io/ismrmrd/mrd-tools mrd_phantom \
    | docker run --rm -i ghcr.io/ismrmrd/mrd-tools mrd_stream_recon \
    | docker run --rm -i -v "${WRITEDIR}":/tmp ghcr.io/ismrmrd/mrd-tools mrd_image_stream_to_png /tmp/image_


if [ ! -f "${READDIR}/image_000000.png" ]; then
    echo "Failed to identify image file(s)"
    exit 1
fi
