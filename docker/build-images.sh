#!/usr/bin/env bash

set -eo pipefail

tag="latest"
image_base_name="ghcr.io/ismrmrd"
push=false

# parse command line arguments
# parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --tag)
            tag="$2"
            shift
            shift
            ;;
        --image-base-name)
            image_base_name="$2"
            shift
            shift
            ;;
        --push)
            push=true
            shift
            ;;
        *)
            echo "Unknown option $key"
            exit 1
            ;;
    esac
done

dockerfile="$(dirname "${BASH_SOURCE[0]}")/Dockerfile"
context="$(dirname "${BASH_SOURCE[0]}")/.."

targets=("mrd-tools")
push_targets=("mrd-tools")

for target in "${targets[@]}"; do
    echo "Building ${target}..."
    docker build -t "${image_base_name}/${target}:${tag}" -f "$dockerfile" "$context" --target "$target"
    if [[ " ${push_targets[@]} " =~ " ${target} " ]] && [ "$push" = true ]; then
        echo "Pushing ${target}..."
        docker push "${image_base_name}/${target}:${tag}"
        docker build -t "${image_base_name}/${target}:latest" -f "$dockerfile" "$context" --target "$target"
        docker push "${image_base_name}/${target}:latest"
    fi
done
