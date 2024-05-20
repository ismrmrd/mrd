## ISMRMRD <-> MRD converter

To enable interoperability with the older [ISMRMRD format](https://github.com/ismrmrd/ismrmrd) format, the MRD repository contains tools for roundtrip conversion between the two formats.

These tools are found in `cpp/mrd-tools/` alongside the example reconstruction program.

```bash
cd cpp/build
ismrmrd_generate_cartesian_shepp_logan -o roundtrip.h5
ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout | ./ismrmrd_to_mrd | ./mrd_to_ismrmrd > roundtrip.bin
ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout > direct.bin

# The files should not be different
diff direct.bin roundtrip.bin
```
