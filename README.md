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

## LICENSE

See [LICENSE](LICENSE).
