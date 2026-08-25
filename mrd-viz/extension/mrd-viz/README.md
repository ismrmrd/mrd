# MRD Viz

A Visual Studio Code extension for inspecting [MRD](https://github.com/ismrmrd/mrd) (Magnetic Resonance Data) files directly in the editor. Open a `.mrd` file to view a thumbnail mosaic of its images alongside acquisition, waveform, and header metadata.

## Features

- Opens `.mrd` files in a custom editor (thumbnail mosaic + metadata panels).
- Select a tile to load its full-resolution image on demand.
- Browse image, acquisition, waveform, and raw-stream metadata, including a raw JSON view.

## Install

Download the VSIX for your platform from the [latest GitHub Release](https://github.com/ismrmrd/mrd/releases/latest), then run **Extensions: Install from VSIX...** in VS Code. Supported platform builds include the backend, so Python setup is not required.

On a platform without a bundled build, run **MRD Viz: Set Up Backend** or point `mrdViz.backendPath` at a Python 3.12 environment containing `mrd_viz`.

## Extension Settings

This extension contributes the following settings:

- `mrdViz.backendPath`: Path to a Python interpreter (runs `python -m mrd_viz.cli`) or a prebuilt `mrd-viz` binary. Leave unset to use the backend bundled with the extension.
- `mrdViz.maxThumbnails`: Maximum number of image thumbnails requested for the initial view (default `128`).
- `mrdViz.backendTimeoutMs`: Timeout in milliseconds for a single backend process (default `30000`).

## Commands

- `MRD Viz: Open File` — open the selected or picked `.mrd` file in MRD Viz.
- `MRD Viz: Set Up Backend` — provision the managed Python fallback.
- `MRD Viz: Select Python Interpreter` — select an existing backend environment.

## Known Issues

- Non-`.mrd` files and non-`file://` resources are rejected with a warning; only local `.mrd` files are supported.

## Release Notes

### 0.0.1

Initial preview: custom editor, thumbnail mosaic, on-demand full-resolution images, and metadata panels.
