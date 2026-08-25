# mrd-viz

Lightweight MRD inspection and preview VS Code extension.

The current focus is direct inspection of existing `.mrd` files rather than reconstruction orchestration. See `docs/TECHNICAL_DESIGN.md` for detailed project context and implementation plan.

## Researcher functionality and onboarding

| Delivery | Before | After | State |
| --- | --- | --- | --- |
| PR #78 dev container | Researchers assembled Python, Node, Azure tools, backend, and extension separately. | One reproducible container and setup command provide a test environment. | Delivered |
| D1 backend resolution | A missing or wrong Python could produce a raw process error or select an unintended fallback. | MRD Viz validates a machine-local override or the bundled backend and provides guided recovery. | Delivered |
| GitHub Release | Researchers built from source or stayed inside a development container. | A version tag builds platform VSIXs and publishes one reviewable GitHub Release. | Ready in this PR |
| D3 bundled backend | Normal VS Code installs required Python and manual backend configuration. | Linux x64, Windows x64, and Apple Silicon VSIXs include a validated standalone backend. | Delivered |
| D2 managed fallback | Unsupported platforms have no bundled binary. | Guided provisioning creates an extension-owned Python environment with cleanup and actionable errors. | Delivered fallback; PyPI publication pending |
| Marketplace | Researchers download and update a VSIX manually. | The release workflow can publish the same reviewed platform artifacts when `VSCE_PAT` is configured. | Prepared; credentials pending |
| Multi-file comparison | Inspection is file-first and one editor at a time. | Compare related files, slices, image types, and metadata in one workflow. | Planned |
| F10 maintainability | Viewer HTML, styles, and behavior shared one large module. | Focused webview modules reduce change risk while preserving the researcher UX. | Delivered |
| Feedback-driven onboarding | Setup assumptions come primarily from developer testing. | Researcher feedback determines defaults, diagnostics, and which fallback paths stay visible. | Starts after release |

## Install the researcher preview

Download the VSIX for your platform from the [latest GitHub Release](https://github.com/ismrmrd/mrd/releases/latest), install it with **Extensions: Install from VSIX...**, and open a `.mrd` file. See the [release guide](docs/RELEASE.md) for publishing and fallback details.