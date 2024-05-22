# Quick Start

## Install

The MRD Python library requires Python >= 3.9 and NumPy >= 1.22.0.

### Anaconda

We recommend using the `mrd-python` Anaconda package, which can be installed using `conda` or `mamba`:

```bash
$ mamba install ismrmrd:mrd-python
```

### PyPI

You can also install `mrd-python` from PyPI, e.g. using `pip`:

```bash
$ python3 -m pip install mrd-python
```

## Reading and Writing MRD streams

To read and write MRD streams, start with the following example:

<<< @/../python/mrd/tools/minimal_example.py

## Examples

See `python/mrd/tools` in the MRD repository for example programs using the `mrd` package.

These tools are also installed as Python modules in the `mrd.tools` package when `mrd-python` is installed from Anaconda or PyPI.

For example, to generate a cartesian Shepp-Logan phantom:

```bash
$ python -m mrd.tools.phantom --coils 8 --matrix 256 > phantom.bin
```
