# ISMRM Raw Data Format (MRD)

MRD is the next generation of the ISMRM Raw Data Format, superseding [ISMRMRD v1](https://ismrmrd.readthedocs.io).


## Getting Started

Please check out the project [documentation](https://ismrmrd.github.io/mrd).

## Building the Code in this Repo

We recommend opening this repository in a [devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) or a [codespace](https://docs.github.com/en/codespaces/overview).

The devcontainer is configured to install all dependencies for this repository, including:
- Those listed in the [Conda](https://docs.conda.io/en/latest/) [environment.yml](environment.yml)
file
- [Yardl](https://github.com/microsoft/yardl/releases) - most recent release
- (Optional) [MATLAB R2023b or newer]

We use the [`just`](https://github.com/casey/just) command runner to build and run tests. To get started, you should be able to run

```bash
$ just
```

from the repo root, or, with MATLAB installed

```bash
$ just matlab=enabled
```

## References

A prerequisite for sharing magnetic resonance (imaging) reconstruction algorithms and code is a common raw data format. This repository describes such a common raw data format, which attempts to capture the data fields that are required to describe the magnetic resonance experiment with enough detail to reconstruct images. The repository also contains a C/C++ library for working with the format. This standard was developed by a subcommittee of the ISMRM Sedona 2013 workshop and is described in detail in:

Inati SJ, Naegele JD, Zwart NR, Roopchansingh V, Lizak MJ, Hansen DC, Liu CY, Atkinson D, Kellman P, Kozerke S, Xue H, Campbell-Washburn AE, Sørensen TS, Hansen MS. ISMRM Raw data format: A proposed standard for MRI raw datasets. [Magn Reson Med. 2017 Jan;77(1):411-421.](https://onlinelibrary.wiley.com/doi/10.1002/mrm.26089)

Please cite this paper if you use the format.

## LICENSE

See [LICENSE](LICENSE).
