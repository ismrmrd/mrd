set shell := ['bash', '-ceuo', 'pipefail']

ensure-build-dir:
    mkdir -p cpp/build

configure: ensure-build-dir
    cd cpp/build; \
    cmake -GNinja  ..

build: configure
    cd cpp/build && ninja

@convert-xsd:
    wget -O ismrmrd.xsd https://raw.githubusercontent.com/ismrmrd/ismrmrd/master/schema/ismrmrd.xsd
    python utils/xsd-to-yardl.py ismrmrd.xsd > model/mrd_header.yml
    rm ismrmrd.xsd

generate: convert-xsd
    cd model && yardl generate
