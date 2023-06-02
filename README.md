# MRD Playground

This repo is an illustration of how [yardl](https://github.com/Microsoft/yardl) could be used to develop the next generation of the [ISMRMRD/MRD](https://github.com/ismrmrd/ismrmrd) standard.

To get started:

1. Open the repo in [GitHub Codespaces](https://docs.github.com/en/codespaces/overview) or a [VS Code Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers).
2. Generate code from the yardl model:
    ```bash
    just generate
    ```
3. Build the project:
    ```bash
    just build
    ```
4. Perform example reconstruction:
    ```bash
    cd cpp/build
    ./mrd_phantom -s | ./mrd_stream_recon | ./mrd_stream_to_hdf5 images.h5
    ```
5. To inspect images, you can use the MRD image stream to PNG converter:
    ```bash
    cd cpp/build
    ./mrd_phantom -s | ./mrd_stream_recon | ./mrd_image_stream_to_png
    ```

## ISMRMRD -> MRD converter

To enable interoperability with the older [ISMRMRD format](https://github.com/ismrmrd/ismrmrd) format, the repo contains tools for rountrip conversion between the two formats:

```bash
cd cpp/build
ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout | ./ismrmrd_to_mrd | ./mrd_to_ismrmrd > roundtrip.bin
ismrmrd_hdf5_to_stream -i roundtrip.h5 --use-stdout > direct.bin

# The files should not be different
diff direct.bin roundtrip.bin
```

You can run the roundtrip tests with:

```bash
just test
```
