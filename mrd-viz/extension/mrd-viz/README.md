# MRD Viz

A Visual Studio Code extension for inspecting [MRD](https://github.com/ismrmrd/mrd) (Magnetic Resonance Data) files directly in the editor. Open a `.mrd` file to view a thumbnail mosaic of its images alongside acquisition, waveform, and header metadata.

## Features

- Opens `.mrd` files in a custom editor (thumbnail mosaic + metadata panels).
- Select a tile to load its full-resolution image on demand.
- Browse image, acquisition, waveform, and raw-stream metadata, including a raw JSON view.

## Requirements

For researcher onboarding, use the stable release installer flow first:

- Open: `https://github.com/ismrmrd/mrd/releases/latest`
- Install the latest MRD Viz release artifact

That path is intended to avoid local Python/PyPI setup.  
For development/debug fallback, MRD Viz can use a Python backend (the `mrd_viz` package) via `mrdViz.backendPath`. During local development (the F5 dev host) the extension also auto-detects `mrd-viz/backend/.venv`.

## Extension Settings

This extension contributes the following settings:

- `mrdViz.backendPath`: Path to a Python interpreter (runs `python -m mrd_viz.cli`) or a prebuilt `mrd-viz` binary. Leave unset to use the backend bundled with the extension.
- `mrdViz.maxThumbnails`: Maximum number of image thumbnails requested for the initial view (default `128`).
- `mrdViz.backendTimeoutMs`: Timeout in milliseconds for a single backend process (default `30000`).

## Commands

- `MRD Viz: Open File` — open the selected or picked `.mrd` file in MRD Viz.
- `MRD Viz: Open Stable Install Link` — open the latest MRD release page for the stable installer path.
- `MRD Viz: Set Up Backend` — choose stable installer, managed local setup, or manual interpreter selection.
- `MRD Viz: Select Python Interpreter` — set `mrdViz.backendPath` manually.
- `MRD Viz: Open Workflow View (D3 Scaffold)` — open the first workflow/session-level D3 panel scaffold.

## Known Issues

- Non-`.mrd` files and non-`file://` resources are rejected with a warning; only local `.mrd` files are supported.

## Release Notes

### 0.0.1

Initial preview: custom editor, thumbnail mosaic, on-demand full-resolution images, and metadata panels.
