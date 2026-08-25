# MRD Viz researcher onboarding and roadmap

This plan keeps the first delivery focused on the smallest experience that already feels useful to researchers:

- D1 delivers a file-first viewer that opens `.mrd` files directly in VS Code.
- Release packages that experience into a `.vsix` that can be installed from GitHub Releases.
- The later milestones can continue in parallel, but they do not block the first researcher-facing release.

## Functionality table

| Milestone | Before UX | After UX | Functions created | Why it matters |
| --- | --- | --- | --- | --- |
| D1 | Researchers need a source checkout, manual backend setup, and a dev-host workflow to inspect `.mrd` files. | Researchers can install the extension, point it at a Python backend, and open a local `.mrd` file in a normal VS Code window. | Custom editor for `.mrd`, open-file command, backend interpreter selection, thumbnail mosaic preview, on-demand full-resolution image loading, metadata panels. | This is the first “real” researcher UX: inspect MRD data without a custom dev environment. |
| Release | There is no simple installable artifact for non-developers. | Researchers can install a packaged `.vsix` from a GitHub Release with a single command such as `code --install-extension mrd-viz-*.vsix`. | VSIX packaging workflow, release automation, packaging runbook, installation guidance. | This removes the biggest onboarding friction for early adopters. |
| D2 | A single file is viewable, but metadata navigation is still coarse. | Researchers can inspect acquisition, waveform, and raw metadata with clearer grouping and search. | Structured metadata summaries, improved panels, richer navigation between preview and metadata. | Makes it easier to understand what a file contains before deeper analysis. |
| D3 | Users can inspect one file at a time, which makes comparison work awkward. | Researchers can compare multiple MRD files side by side or in a multi-file review flow. | Multi-file selection, comparison view, synchronized thumbnail and metadata inspection. | Reduces manual effort when comparing reconstructions or runs. |
| Marketplace | Distribution is limited to local installs and GitHub Releases. | Researchers can discover and install the extension from the VS Code Marketplace. | Publisher setup, Marketplace publishing flow, marketplace metadata and branding. | This broadens reach once the core experience is stable. |
| F10 | Backend setup is still a manual step and the first-run experience is uneven. | Researchers get guided backend bootstrap, clearer first-run messages, and fewer setup failures. | Backend auto-detection, setup wizard, robust setup diagnostics, clearer error pages. | This closes the remaining onboarding gap for less technical users. |
| Future ops / support | Researchers can open files, but support and diagnostics are ad hoc. | Teams can collect clear logs, report failures, and troubleshoot the backend more easily. | Better diagnostics, telemetry-safe logging, support docs, known-issue guidance. | Keeps the workflow sustainable as adoption grows. |

## Recommended shipping order

1. Ship D1 + Release together as the first researcher-facing milestone.
2. Keep D2 and D3 moving in parallel behind that milestone so feedback can guide the next iteration.
3. Treat Marketplace and F10 as follow-on work that improves discoverability and onboarding after the core flow is proven.
