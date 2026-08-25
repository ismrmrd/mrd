# MRD Viz

A Visual Studio Code extension for inspecting [MRD](https://github.com/ismrmrd/mrd) (Magnetic Resonance Data) files directly in the editor. Open a `.mrd` file to view a thumbnail mosaic of its images alongside acquisition, waveform, and header metadata.

## Features

- Opens `.mrd` files in a custom editor (thumbnail mosaic + metadata panels).
- Select a tile to load its full-resolution image on demand.
- Browse image, acquisition, waveform, and raw-stream metadata, including a raw JSON view.
- Start the D3 comparison scaffold by selecting multiple `.mrd` files and opening the new compare view.

## Quick start for researchers

The first researcher-friendly path is a packaged VSIX from a GitHub Release:

1. Download the latest `mrd-viz-*.vsix` from the MRD Viz GitHub Release assets.
2. Install it with `code --install-extension mrd-viz-*.vsix`.
3. Create or point MRD Viz at a Python 3.12 environment that has the `mrd_viz` backend installed.
4. Open a local `.mrd` file (or run `MRD Viz: Open File`) to view it in a regular VS Code window.

For the backend setup, the extension looks for the interpreter configured in `mrdViz.pythonPath`; a local development checkout can also auto-detect `mrd-viz/backend/.venv`.

See [mrd-viz/docs/RESEARCHER_ONBOARDING_AND_ROADMAP.md](../../docs/RESEARCHER_ONBOARDING_AND_ROADMAP.md) for the phased D1/release roadmap and the broader functionality plan.

## Requirements

MRD Viz relies on a Python backend (the `mrd_viz` package) to read `.mrd` files. You need:

- Python 3.12
- The `mrd_viz` backend installed into an environment the extension can find.

Point the extension at the interpreter with the `mrdViz.pythonPath` setting (see below). During local development the extension also auto-detects a virtual environment at `mrd-viz/backend/.venv`.

## Extension Settings

This extension contributes the following settings:

- `mrdViz.pythonPath`: Python executable used to run `python -m mrd_viz.cli`. Set this to the backend environment's interpreter.
- `mrdViz.maxThumbnails`: Maximum number of image thumbnails requested for the initial view (default `128`).
- `mrdViz.backendTimeoutMs`: Timeout in milliseconds for a single backend process (default `30000`).

## Commands

- `MRD Viz: Open File` — open the selected or picked `.mrd` file in MRD Viz.

## Known Issues

- Non-`.mrd` files and non-`file://` resources are rejected with a warning; only local `.mrd` files are supported.

## Release Notes

### 0.0.1

Initial preview: custom editor, thumbnail mosaic, on-demand full-resolution images, and metadata panels.
