# MRD Viz

A Visual Studio Code extension for inspecting [MRD](https://github.com/ismrmrd/mrd) (Magnetic Resonance Data) files directly in the editor. Open a `.mrd` file to view a thumbnail mosaic of its images alongside acquisition, waveform, and header metadata.

## Features

- Opens `.mrd` files in a custom editor (thumbnail mosaic + metadata panels).
- Select a tile to load its full-resolution image on demand.
- Browse image, acquisition, waveform, and raw-stream metadata, including a raw JSON view.

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
