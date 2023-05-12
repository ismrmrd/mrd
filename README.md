# MRD Playground

This repo is an illustration of how [yardl](https://github.com/Microsoft/yardl) could be used to develop the next generation of the [ISMRMRD/MRD](https://github.com/ismrmrd/ismrmrd) standard.

To get started:

1. Open the repo in [GitHub Codespaces](https://docs.github.com/en/codespaces/overview) or a [VS Code Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers).
2. Generate code from the yardl model:
    ```
    just generate
    ```
3. Build the project:
    ```
    just build
    ```
4. Perform example reconstruction:
    ```
    cd cpp/build
    ./mrd_phantom -s | ./mrd_stream_recon | ./mrd_stream_to_hdf5 images.h5
    ```
5. Display the images using the [display.ipynb](display.ipynb) notebook
