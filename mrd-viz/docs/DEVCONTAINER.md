# MRD Viz Dev Container (Scenario B)

Run MRD Viz inside a reproducible dev container: Python 3.12 + the `mrd_viz` backend + the MRD Viz extension + Azure tooling (`az` / `azcopy`), all wired together. This is the recommended way for the research team to use MRD Viz against `.mrd` data stored in Azure.

## Prerequisites

- Docker
- The **Dev Containers** VS Code extension (`ms-vscode-remote.remote-containers`)

## 1. Open in the container

1. Open the `mrd` repo in VS Code.
2. Command Palette → **Dev Containers: Reopen in Container** → pick **"MRD Viz extension"**.
   - The other option, **"mrd"**, is the full-repo toolchain container (conda + MATLAB + C++) and is not needed just to view `.mrd` files.
3. Wait for the build. `postCreate` installs the `just` and `azcopy` CLIs, then best-effort provisions the backend virtualenv at `~/.venvs/mrd-viz` (needs PyPI access; the banner it prints says whether it succeeded).

## 2. One-time setup

`postCreate` already provisions the backend virtualenv at `~/.venvs/mrd-viz` and `mrdViz.backendPath` points at it, so opening a `.mrd` file works out of the box. To build and install the **MRD Viz extension** itself — and to (re)run the backend install if the automatic step was skipped or failed on a restricted network — run from the container's integrated terminal:

```bash
just mrd-viz-container-setup
```

This (re)creates the backend virtualenv, installs the `mrd_viz` backend into it, builds the extension `.vsix`, and installs it in this window. Reload the window if the extension does not activate immediately.

> If the `postCreate` banner reported that automatic backend setup did **not** complete (e.g. a blocked network), running `just mrd-viz-container-setup` is required — see [Restricted / corporate networks](#restricted--corporate-networks) below.

## 3. Pull `.mrd` data from Azure

Authenticate and copy files into the `mrd-viz/data/` directory (git-ignored):

```bash
az login            # or use a SAS URL
azcopy copy "<source>" /workspaces/mrd/mrd-viz/data --recursive
```

## 4. Open a file

Double-click any `.mrd` file, or run **MRD Viz: Open File** from the Command Palette.

## Restricted / corporate networks

Some corporate networks block direct access to the **public npm registry** (`registry.npmjs.org`) and require an internal mirror instead. Symptom: the container build or `just mrd-viz-container-setup` fails with an `npm` **TLS handshake failure** to `registry.npmjs.org`. (PyPI is typically unaffected, so the backend install still works.)

To fix it, point the container's npm at your organization's feed with a **git-ignored** `.npmrc`:

1. Find your feed on the host: `npm config get registry`.
2. Create `mrd-viz/extension/mrd-viz/.npmrc` (git-ignored) with:

   ```ini
   registry=https://your-org-feed.example/npm/
   ```

3. Run `just mrd-viz-container-setup` again.

If your feed requires authentication, add the appropriate `_authToken`/credential-provider lines (same as your host `.npmrc`). This file is git-ignored so the internal URL is never committed.

## Backend error: a host path or `spawn ... ENOENT`

If opening a `.mrd` file fails and the **Running:** line in the error shows a **host path** (e.g. a Windows `...\.venv\Scripts\python.exe`) instead of `/home/vscode/.venvs/mrd-viz/bin/python`, a host interpreter path is leaking into the container. `mrdViz.backendPath` is **machine-scoped**, so it cannot be set from a committed workspace `.vscode/settings.json` and cannot leak across the host/container boundary — a leak today comes only from a legacy, deprecated `mrdViz.pythonPath` left in workspace settings.

Fix: remove any `mrdViz.pythonPath` from the workspace `.vscode/settings.json`, then reload the window. Point the container at its interpreter with `mrdViz.backendPath` in the container's remote (or your **User**) settings instead; because it is machine-scoped it stays per-machine and never leaks.

## Notes

- The extension is **built from source** in the container (needs Node). Planned follow-up: attach a prebuilt `.vsix` to a GitHub Release so the container can install it without building.
- For manual/local (non-container) setup, see [PACKAGING_AND_INSTALL_RUNBOOK.md](PACKAGING_AND_INSTALL_RUNBOOK.md) and [OFFICIAL_EXT_DEV_RUNBOOK.md](OFFICIAL_EXT_DEV_RUNBOOK.md).
