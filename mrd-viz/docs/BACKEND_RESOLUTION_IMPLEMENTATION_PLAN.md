# MRD Viz — Deterministic Backend Resolution: Implementation Plan

Implementation plan for replacing the 5-candidate backend search with a deterministic, fail-loud
resolver. Design rationale and diagrams live in
[BACKEND_INSTALL_MODES.md](BACKEND_INSTALL_MODES.md) (see "Target architecture"); this document is
the build plan.

## Invariant

- **One source of truth:** the `mrd_viz` Python package (`mrd-viz/backend`). The bundled binary is a
  PyInstaller *snapshot* of that exact package ([`packaging/entry.py`](../backend/packaging/entry.py)
  → `mrd_viz.cli:main`), so developer edits are reflected on the next binary rebuild.
- **Resolution consults at most two candidates**, in a fixed order, and **never silently falls back**
  across the developer/end-user boundary.
- **Every failure is loud** and offers exactly one next action.

## Confirmed decisions

1. **Rename** `mrdViz.pythonPath` → **`mrdViz.backendPath`** (accepts an interpreter *or* a binary
   path). Read the old `mrdViz.pythonPath` for backward compatibility.
2. **Dev convenience gated on `context.extensionMode === Development`** (set by VS Code for the F5
   host, not derived from any setting). Repo `backend/.venv` is consulted only in Development mode
   and only when `backendPath` is unset.
3. **`backendPath` is `"scope": "machine"`**, and provisioning/selection persists the resolved path
   via `ConfigurationTarget.Global` (which routes to host user settings or the container's remote
   settings automatically). This structurally prevents the workspace→container path leak and keeps
   the path out of Settings Sync.
4. **Old-glibc Linux binary is an odin dependency**, not a bespoke mrd-viz build. Until odin ships a
   compatible build, old-glibc Linux end users hit the fail-loud → guided-setup/override path.

## Resolution model

```
Production (installed VSIX):
    1. backendPath set?  -> probe; ok -> use;  fail -> FAIL LOUD (no fallback)
    2. bundled binary?   -> probe; ok -> use;  fail/absent -> FAIL LOUD (offer recovery)

Development (F5 host):
    1. backendPath set?  -> probe; ok -> use;  fail -> FAIL LOUD (no fallback)
    (dev) backendPath UNSET -> repo backend/.venv -> probe; ok -> use
    2. bundled binary?   -> probe; ok -> use;  fail/absent -> FAIL LOUD (offer recovery)
```

"Probe" = run the candidate with `--version` under a short timeout and require exit code 0 (the
existing `validateBackend`). Both delivery forms expose the identical CLI
([`cli.py`](../backend/src/mrd_viz/cli.py)); binary uses `baseArgs: []`, interpreter uses
`baseArgs: ['-m', 'mrd_viz.cli']`.

---

## Phase 0 — Preconditions

- **P0.1 (external, odin):** track the old-glibc Linux binary as an upstream odin dependency. Do
  **not** add a custom low-glibc build to mrd-viz. The deterministic resolver degrades gracefully
  (fail loud + offer override/guided setup) where no compatible binary exists, so this does not
  block the rest of the work — it only bounds which platforms get the zero-config default.
- **P0.2 CLI parity test:** assert `python -m mrd_viz.cli --version` and the built binary agree, so
  the two delivery forms can't diverge silently. Lives with the backend tests.

## Phase 1 — Settings schema (`package.json`)

- Add `mrdViz.backendPath`:
  - `"type": "string"`, **no default** (unset must mean "unset", fixing the `default: "python"`
    trap), `"scope": "machine"`.
  - `markdownDescription`: "Developer override — path to a Python interpreter (runs
    `python -m mrd_viz.cli`) or a prebuilt backend binary. Leave unset to use the backend bundled
    with the extension."
- Keep `mrdViz.pythonPath` declared but mark it deprecated (`markdownDeprecationMessage`) and read it
  as a fallback for one release.
- No change to `mrdViz.maxThumbnails` / `mrdViz.backendTimeoutMs`.

## Phase 2 — Resolver rewrite ([`backendResolver.ts`](../extension/mrd-viz/src/backendResolver.ts))

- Replace `backendCandidates()` (5 candidates) with an ordered builder that takes
  `context.extensionMode`:
  - `getConfiguredBackendPath()`: read `backendPath` (then legacy `pythonPath`) via `get()`; missing
    → `undefined`. Classify interpreter vs. binary by basename (`mrd-viz` / `mrd-viz.exe`) or
    extension, producing `baseArgs` accordingly.
  - Bundled binary via existing `bundledBinaryPath()`.
  - Dev-only: `developmentVenvPython()` **only** when `extensionMode === Development` and
    `backendPath` is unset.
- **No cross-tier fallback:** if `backendPath` is set and its probe fails, return
  `{ ok:false, tried:[thatAttempt] }` — do not try the binary. Encode the failing tier so the UI can
  tailor the message.
- Delete the managed-venv candidate and the `python`/`python3` PATH candidates from resolution.
- Keep `validateBackend`, `invalidateBackendCache`, and the `BackendAttempt` shape.

## Phase 3 — Fail-loud UX

- `getMrdBackendMissingHtml` ([`webviewHtml.ts`](../extension/mrd-viz/src/webviewHtml.ts)) grows two
  shapes, each with one action:
  - **Developer override broken:** show the configured path + probe error → "Select Python
    Interpreter…".
  - **End user, no runnable binary:** (unsupported platform / missing binary) → one recovery:
    guided setup.
- `provisionManagedBackend` ([`extension.ts`](../extension/mrd-viz/src/extension.ts)) on success
  **writes the venv path to `backendPath` (`ConfigurationTarget.Global`)**, collapsing the managed
  venv into tier 1. It stays a *recovery command*, not a resolver candidate.
- `selectInterpreter` writes `backendPath` (`Global`) and **drops** the manual Workspace/
  WorkspaceFolder clearing (unnecessary once the setting is machine-scoped).
- The re-resolve-after-setup flow in [`mrdEditorProvider.ts`](../extension/mrd-viz/src/mrdEditorProvider.ts)
  is unchanged in shape.

## Phase 4 — Environments

- **Dev container:** stop hard-coding `mrdViz.pythonPath` in
  [`.devcontainer/mrd-viz/devcontainer.json`](../../.devcontainer/mrd-viz/devcontainer.json). Let
  `postCreate` provisioning write `backendPath` to the container's remote settings (verify how the
  installed VS Code applies dev-container settings vs. `machine` scope during implementation).
- **F5 contributors:** covered by the Development-mode repo-`.venv` gate; no committed workspace
  setting needed.

## Phase 5 — Cleanup & docs

- Remove dead resolver code (managed-venv candidate, PATH candidates; keep helpers still used by
  provisioning).
- Update the "current state" half of [BACKEND_INSTALL_MODES.md](BACKEND_INSTALL_MODES.md) to match,
  plus [DEVCONTAINER.md](DEVCONTAINER.md) and the runbooks.
- Tests: resolver unit tests for the two-tier order, the no-fallback rule, and the Development gate;
  keep the command-registration test in
  [`extension.test.ts`](../extension/mrd-viz/src/test/extension.test.ts).

## Phase 6 — Verification matrix

| Scenario | Expected |
|---|---|
| Installed VSIX, no Python on host | bundled binary runs (zero config) |
| `backendPath` set but broken | fail loud; **no** silent binary use |
| Dev container | uses the configured/provisioned container venv |
| F5 from source, `backendPath` unset | uses repo `backend/.venv` (Development gate) |
| Old-glibc Linux, no odin binary yet | fail loud → guided setup / override |
| Workspace `.vscode/settings.json` sets a path | ignored (machine scope) — no container leak |

## Suggested PR sequencing (small, reviewable)

1. **Schema + resolver core** (Phases 1–2): rename to `backendPath`, machine scope, two-tier
   resolver, no-fallback, dev gate. Legacy `pythonPath` read retained.
2. **Fail-loud UX + persistence** (Phase 3): tailored missing-backend pages; provisioning/selection
   persist `backendPath`; drop scope-clearing.
3. **Environments + docs + tests** (Phases 4–5): dev container change, doc updates, resolver tests.

## Open items to confirm before/while building

- Exact interpreter-vs-binary classification for `backendPath` (basename heuristic vs. an explicit
  companion setting).
- Empirical check of dev-container settings application vs. `machine` scope (Phase 4).
- How long to retain the deprecated `mrdViz.pythonPath` read.
