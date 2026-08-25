# MRD Viz

A Visual Studio Code extension for inspecting [MRD](https://github.com/ismrmrd/mrd) (Magnetic Resonance Data) files directly in the editor. Open a `.mrd` file to view a thumbnail mosaic of its images alongside acquisition, waveform, and header metadata.

## Features

- Opens `.mrd` files in a custom editor (thumbnail mosaic + metadata panels).
- Select a tile to load its full-resolution image on demand.
- Browse image, acquisition, waveform, and raw-stream metadata, including a raw JSON view.

## Requirements

MRD Viz relies on a Python backend (the `mrd_viz` package) to read `.mrd` files.

- Python 3.12
- A reachable `mrd_viz` backend (managed setup, local wheel, or pre-installed interpreter)

You can run **MRD Viz: Set Up Backend** to create a managed backend automatically. If you already have an environment, point `mrdViz.pythonPath` at that interpreter (see below). During local development the extension also auto-detects a virtual environment at `mrd-viz/backend/.venv`.

## Extension Settings

This extension contributes the following settings:

- `mrdViz.pythonPath`: Python executable used to run `python -m mrd_viz.cli`. Set this to the backend environment's interpreter.
- `mrdViz.maxThumbnails`: Maximum number of image thumbnails requested for the initial view (default `128`).
- `mrdViz.backendTimeoutMs`: Timeout in milliseconds for a single backend process (default `30000`).

## Commands

- `MRD Viz: Open File` — open the selected or picked `.mrd` file in MRD Viz.
- `MRD Viz: Set Up Backend` — provision a managed backend or install from a local wheel.
- `MRD Viz: Select Python Interpreter` — set `mrdViz.pythonPath` manually.
- `MRD Viz: Open Workflow View (D3 Scaffold)` — open the workflow-level placeholder panel for upcoming D3 UX.

## Known Issues

- Non-`.mrd` files and non-`file://` resources are rejected with a warning; only local `.mrd` files are supported.

## Release Notes

### 0.0.1

Initial preview: custom editor, thumbnail mosaic, on-demand full-resolution images, and metadata panels.
