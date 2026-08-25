# mrd-viz

Lightweight MRD inspection and preview VS Code extension.

The current focus is direct inspection of existing `.mrd` files rather than reconstruction orchestration. See `docs/TECHNICAL_DESIGN.md` for detailed project context and implementation plan.  

## Functionality / UX progression

| Track | Before UX | After UX | Status |
| --- | --- | --- | --- |
| **PR78 checkpoint** | Dev-container-first onboarding (`just mrd-viz-container-setup`) | Extension/backend become usable across windows attached to the same dev container | Delivered |
| **PR79 + D3 consolidated** | Users could end up in Python/PyPI/manual interpreter flows | **Stable install path added as the primary UX** via `https://github.com/ismrmrd/mrd/releases/latest`, with in-product “Open Stable Install Link” guidance | Delivered |
| **D1 local fallback** | Backend setup was mostly manual | Command-driven managed setup + manual override remain available for development/debug paths | Delivered |
| **D3 workflow surface** | File-first custom editor only | Added workflow/session-level panel scaffold (`Open Workflow View (D3 Scaffold)`) to iterate on run-level UX | Scaffolded |
| **D2** | No dedicated multi-file comparison workflow | Planned deeper multi-file comparison UX on top of current viewer contracts | Planned |
| **Marketplace** | Side-load/release flow primary | Planned one-click marketplace install/update once publisher path is finalized | Planned |
| **F10 onboarding polish** | Onboarding still split across docs + commands | Planned final simplification from researcher feedback rounds | Planned |