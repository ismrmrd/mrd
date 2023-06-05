set shell := ['bash', '-ceuo', 'pipefail']

@default: test

@ensure-build-dir:
    mkdir -p cpp/build

@configure: ensure-build-dir
    cd cpp/build; \
    cmake -GNinja  ..

@build: configure
    cd cpp/build && ninja

@convert-xsd:
    wget -O ismrmrd.xsd https://raw.githubusercontent.com/ismrmrd/ismrmrd/master/schema/ismrmrd.xsd
    python utils/xsd-to-yardl.py ismrmrd.xsd > model/mrd_header.yml
    rm ismrmrd.xsd

@generate:
    cd model && yardl generate

@converter-roundtrip-test:
    cd cpp/build; \
    rm -f roundtrip.h5; \
    rm -f roundtrip.bin; \
    rm -f direct.bin; \
    rm -f recon_direct.bin; \
    rm -f recon_rountrip.bin; \
    ismrmrd_generate_cartesian_shepp_logan -o roundtrip.h5; \
    ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout | ./ismrmrd_to_mrd | ./mrd_to_ismrmrd > roundtrip.bin; \
    ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout > direct.bin; \
    ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout | ismrmrd_stream_recon_cartesian_2d --use-stdin --use-stdout > recon_direct.bin; \
    ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout | ismrmrd_stream_recon_cartesian_2d --use-stdin --use-stdout | ./ismrmrd_to_mrd | ./mrd_to_ismrmrd > recon_rountrip.bin; \
    diff direct.bin roundtrip.bin & diff recon_direct.bin recon_rountrip.bin

@test: generate build converter-roundtrip-test
