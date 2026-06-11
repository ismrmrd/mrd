# Upgrading MRD Binary Files

MRD binary files embed the full schema as a JSON string. The MRD SDK validates that the
schema in a file exactly matches the one compiled into the library, so a file produced with
an older version of the SDK will be rejected by a newer one with an error like:

```
ValueError: Schema mismatch ...
```

`mrd-upgrade` is a command-line tool that upgrades an older MRD binary file to the current
schema version. It fully decodes the old binary layout and re-encodes it in the new format.
No data is lost: new optional fields introduced between versions are set to `None` on
upgraded records.

## Installation

`mrd-upgrade` is included with the `mrd` Python package:

```bash
pip install mrd-python
```

## Usage

```bash
# Upgrade to a new file (default output name: <input>.upgraded)
mrd-upgrade scan.mrd

# Specify an explicit output path
mrd-upgrade scan.mrd scan_new.mrd

# Replace the original file in-place (atomic swap)
mrd-upgrade --in-place scan.mrd
```

Run `mrd-upgrade --help` for full usage information.

## Supported upgrade paths

| From    | To      |
|---------|---------|
| v2.2.0  | v2.2.1  |

If your file version is not listed, `mrd-upgrade` will report an error.

## What changes during an upgrade

The following fields are new in v2.2.1. They will be `None` on every upgraded record, since
they were not present in the source file:

- `AcquisitionHeader.acquisition_center_frequency`
- `Acquisition.phase`

All other data is preserved exactly.

## Checking a file's schema version

You can check the schema version of any MRD binary file from Python:

```python
from mrd.tools.upgrade import identify_file_version

version = identify_file_version("scan.mrd")
print(version)  # e.g. "2.2.0" or "2.2.1", or None if unrecognised
```
