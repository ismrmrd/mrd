# MRD Tools

MRD includes useful tools for working with MRD streams.

These tools are available in the [MRD conda package](https://anaconda.org/ismrmrd/mrd) and in the [MRD Docker image](https://ghcr.io/ismrmrd/mrd).

The source for each tool can be found in the `cpp/mrd-tools` subdirectory of the MRD repository.

## Generating a Phantom

To quickly generate a cartesian Shepp-Logan phantom (k-space data), use `mrd_phantom`.

Optionally specify the number of coils, matrix size, number of repetitions, and oversampling factor.

```bash
$ mrd_phantom -c 8 -m 256 -r 2 -s 2 > phantom.bin
# OR
$ mrd_phantom --coils 8 --matrix 256 --repetitions 2 --oversampling 2 > phantom2.bin
```

## Stream Reconstruction

To reconstruct 2D images (such as a cartesian phantom generated using `mrd_phantom`), use `mrd_stream_recon`.

This tool reads an MRD stream of Acquisitions from `stdin` and writes the output MRD stream of Images to `stdout`.

```bash
$ cat phantom.bin | mrd_stream_recon > images.bin
```

## Convert Images to PNG

To easily view Images in an MRD stream, use `mrd_image_stream_to_png` to convert them to PNG files.

This tool reads an MRD stream of Images from `stdin` and writes the output PNG files to disk.

```bash
$ cat images.bin | mrd_image_stream_to_png ./result
$ ls
result000000.png  result000001.png
```

## ISMRMRD <-> MRD converter

To enable interoperability with the older [ISMRMRD format](https://github.com/ismrmrd/ismrmrd), the MRD repository contains tools for roundtrip conversion between the two formats.
- `mrd_to_ismrmrd`: Convert a binary MRD stream (`stdin`) to an ISMRMRD stream (`stdout`)
- `ismrmrd_to_mrd`: Convert an ISMRMRD stream (`stdin`) to an MRD stream (`stdout`)

```bash
# Use ISMRMRD tools to generate a dataset and convert it to a stream
$ ismrmrd_generate_cartesian_shepp_logan -o phantom.h5
$ ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout > direct.bin

# This time, convert the ISMRMRD stream to MRD, then back again
$ ismrmrd_hdf5_to_stream -i phantom.h5 --use-stdout | ismrmrd_to_mrd | mrd_to_ismrmrd > roundtrip.bin

# The files are identical
$ diff direct.bin roundtrip.bin
```
