# mrd-viz

Lightweight MRD inspection and preview VS Code extension.

The current focus is direct inspection of existing `.mrd` files rather than reconstruction orchestration. See `docs/TECHNICAL_DESIGN.md` for detailed project context and implementation plan.  

## Researcher rollout table

| Track | Before UX / capability | After UX / capability | Status |
| --- | --- | --- | --- |
| **D1 - backend onboarding** | Users had to manually create a Python 3.12 environment, install `mrd_viz`, and set `mrdViz.pythonPath`. | **Set Up Backend** now offers managed setup in-extension (auto install) or install from a local backend wheel, then configures `mrdViz.pythonPath` automatically. | **Delivered** |
| **Release bundle** | Release mostly centered on extension packaging (`.vsix`) and separate backend instructions. | Release workflow now ships a single researcher bundle (`.vsix` + backend wheel/sdist + install guide) as GitHub release assets. | **Delivered** |
| **D2 - comparison / multi-file workflows** | Single-file, single-editor viewing workflow. | Planned expansion into richer multi-file/multi-image inspection and comparison surfaces. | Planned |
| **D3 - workflow-level views** | File-first inspection only. | Added command + panel scaffold for workflow/session UX so we can iterate with researcher feedback without destabilizing file-first flows. | **Scaffolded** |
| **Marketplace** | Side-load install (`code --install-extension ...vsix`) required. | One-click install/update path through VS Code Marketplace after publisher publishing is enabled. | Planned |
| **F10 - onboarding polish** | Setup paths are functional but still rely on explicit user actions. | Planned final UX pass to minimize setup friction further (feedback-driven onboarding refinements). | Planned |