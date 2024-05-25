#!/usr/bin/env bash

set -e

pushd ./python/
python3 -m pip install --upgrade pip
python3 -m pip install build
python3 -m build
popd
