# MRD Viz Dev Container (Scenario B)

Run MRD Viz inside a reproducible dev container: Python 3.12 + the `mrd_viz` backend + the MRD Viz extension + Azure tooling (`az` / `azcopy`), all wired together. This is the recommended way for the research team to use MRD Viz against `.mrd` data stored in Azure.

## Prerequisites

- Docker
- The **Dev Containers** VS Code extension (`ms-vscode-remote.remote-containers`)

## 1. Open in the container

1. Open the `mrd` repo in VS Code.
2. Command Palette → **Dev Containers: Reopen in Container** → pick **"MRD Viz extension"**.
   - The other option, **"mrd"**, is the full-repo toolchain container (conda + MATLAB + C++) and is not needed just to view `.mrd` files.
3. Wait for the build. `postCreate` installs the `just` and `azcopy` CLIs.

## 2. One-time setup

From the integrated terminal (now connected to the container):

```bash
cd mrd-viz
just container-setup
```

This creates a backend virtualenv at `~/.venvs/mrd-viz`, installs the `mrd_viz` backend into it, builds the extension `.vsix`, and installs it in this window. `mrdViz.pythonPath` is already pointed at that venv, so no further configuration is needed. Reload the window if the extension does not activate immediately.

## 3. Pull `.mrd` data from Azure

Authenticate and copy files into a working directory (`./data` is git-ignored):

```bash
azcopy login            # or use a SAS URL
azcopy copy "<source>" ./data --recursive
```

## 4. Open a file

Double-click any `.mrd` file, or run **MRD Viz: Open File** from the Command Palette.

## Notes

- The extension is **built from source** in the container (needs Node). Planned follow-up: attach a prebuilt `.vsix` to a GitHub Release so the container can install it without building.
- For manual/local (non-container) setup, see [PACKAGING_AND_INSTALL_RUNBOOK.md](PACKAGING_AND_INSTALL_RUNBOOK.md) and [OFFICIAL_EXT_DEV_RUNBOOK.md](OFFICIAL_EXT_DEV_RUNBOOK.md).
