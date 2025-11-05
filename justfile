set shell := ['bash', '-ceuo', 'pipefail']

# Read version from file and export for all tasks
export MRD_VERSION_STRING := `cat VERSION`

cpp_version := "20"
build_type := "RelWithDebInfo"

matlab := "disabled"
matlab-test-cmd := if matlab != "disabled" { "run-matlab-command buildtool" } else { "echo Skipping MATLAB tests..." }
cross-recon-test-cmd := if matlab != "disabled" { "MRD_MATLAB_ENABLED=true ./test.sh" } else { "./test.sh" }

@default: test

@ensure-build-dir:
    mkdir -p cpp/build

@configure: ensure-build-dir
    cd cpp/build; \
    cmake -GNinja \
        -D CMAKE_BUILD_TYPE={{ build_type }} \
        -D CMAKE_CXX_STANDARD={{ cpp_version }} \
        -D CMAKE_INSTALL_PREFIX=$(conda info --json | jq -r .default_prefix) \
        ..

@build: configure generate
    cd cpp/build && ninja

@install: test
    cd cpp/build && ninja install

@convert-xsd:
    wget -O ismrmrd.xsd https://raw.githubusercontent.com/ismrmrd/ismrmrd/master/schema/ismrmrd.xsd
    python utils/xsd-to-yardl.py ismrmrd.xsd > model/mrd_header.yml
    rm ismrmrd.xsd

@generate:
    cd model && yardl generate

cpp-converter-roundtrip-test: build
    #!/usr/bin/env bash
    set -euo pipefail
    cd cpp/build
    rm -f phantom.h5
    rm -f direct.ismrmrd
    rm -f roundtrip.ismrmrd
    rm -f recon_direct.ismrmrd
    rm -f recon_rountrip.ismrmrd
    ismrmrd_generate_cartesian_shepp_logan -o phantom.h5
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout > direct.ismrmrd
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | ./ismrmrd_to_mrd | ./mrd_to_ismrmrd > roundtrip.ismrmrd
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | ismrmrd_stream_recon_cartesian_2d --use-stdin --use-stdout > recon_direct.ismrmrd
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | ismrmrd_stream_recon_cartesian_2d --use-stdin --use-stdout | ./ismrmrd_to_mrd | ./mrd_to_ismrmrd > recon_rountrip.ismrmrd
    diff direct.ismrmrd roundtrip.ismrmrd && diff recon_direct.ismrmrd recon_rountrip.ismrmrd

python-converter-roundtrip-test: build
    #!/usr/bin/env bash
    set -euo pipefail
    export PYTHONPATH=$(realpath ./python)
    cd cpp/build
    rm -f phantom.h5
    rm -f direct.ismrmrd
    rm -f roundtrip.ismrmrd
    rm -f recon_direct.ismrmrd
    rm -f recon_rountrip.ismrmrd
    ismrmrd_generate_cartesian_shepp_logan -o phantom.h5
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout > direct.ismrmrd
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | python -m mrd.tools.ismrmrd_to_mrd | python -m mrd.tools.mrd_to_ismrmrd > roundtrip.ismrmrd
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | ismrmrd_stream_recon_cartesian_2d --use-stdin --use-stdout > recon_direct.ismrmrd
    ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | ismrmrd_stream_recon_cartesian_2d --use-stdin --use-stdout | python -m mrd.tools.ismrmrd_to_mrd | python -m mrd.tools.mrd_to_ismrmrd > recon_rountrip.ismrmrd
    python ../../test/diff-ismrmrd-streams.py direct.ismrmrd roundtrip.ismrmrd
    python ../../test/diff-ismrmrd-streams.py recon_direct.ismrmrd recon_rountrip.ismrmrd

@conda-cpp-test: build
    cd cpp/build; \
    PATH=./:$PATH ../conda/run_test.sh

@conda-python-test: generate
    cd python; \
    ./conda/run_test.sh

@matlab-test: generate
    cd matlab; \
    {{ matlab-test-cmd }}

@cross-language-recon-test: build
    cd test; \
    {{ cross-recon-test-cmd }}

@test: build cpp-converter-roundtrip-test python-converter-roundtrip-test conda-cpp-test conda-python-test matlab-test cross-language-recon-test

@validate: test

validate-with-no-changes: validate
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ `git status --porcelain` ]]; then
      echo "ERROR: Found uncommitted changes:"
      git status --porcelain
      exit 1
    fi

@clean:
    rm -rf cpp/conda/build_pkg/
    rm -rf python/conda/build_pkg/
    rm -rf python/dist python/mrd.egg-info/
    pushd cpp/build && ninja clean && popd

@start-docs-website:
    cd docs && npm install && npm run docs:dev

@build-docs:
    cd docs && npm install && npm run docs:build

@build-cpp-conda-package:
    bash -il ./utils/conda/setup-conda-build.sh; \
    cd cpp/conda; \
    ../../utils/conda/package.sh

@build-python-conda-package:
    bash -il ./utils/conda/setup-conda-build.sh; \
    cd python/conda; \
    ../../utils/conda/package.sh

@build-pypi-package:
    ./utils/pypi/package.sh

@localinstall-python-package:
    cd python; \
    pip install .

@build-matlab-toolbox:
    cd matlab; \
    run-matlab-command buildtool

@build-cmake-fetch-src:
    tar -czf mrd-cmake-src-${MRD_VERSION_STRING}.tar.gz -C ./cpp/ CMakeLists.txt mrd/ mrd-tools/

@build-docker-images *PARAMETERS:
    ./docker/build-images.sh {{PARAMETERS}}

@test-docker-images:
    ./docker/test-docker-images.sh
