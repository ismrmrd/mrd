# Packaging & Local Install Runbook (VSIX)

Use this runbook to package the MRD Viz extension into an installable `.vsix` and install it into a normal VS Code instance — so MRD Viz works in **every** VS Code window without launching an Extension Development Host (F5).

This is the distribution counterpart to the [Official Extension Development Runbook](OFFICIAL_EXT_DEV_RUNBOOK.md). Use that runbook to set up the backend and generate test `.mrd` files; use this one to build and install the extension.

> A `.vsix` is the standard way to distribute an extension **without** publishing to the Marketplace. Publishing (`vsce publish`) is a later, separate step that requires a registered publisher and is not covered here.

## 1. Open a Shell at the Extension Folder

Windows PowerShell:

```powershell
$repoRoot = git rev-parse --show-toplevel
Set-Location (Join-Path $repoRoot "mrd-viz/extension/mrd-viz")
```

Linux / macOS Bash:

```bash
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root/mrd-viz/extension/mrd-viz"
```

## 2. Install Extension Dependencies

The build (invoked automatically during packaging) needs the dev dependencies present.

```bash
npm ci
```

Expected result: dependencies install and `npm audit` reports no vulnerabilities.

## 3. Dry Run — List the Files That Would Be Packaged

Before building, confirm the `.vsix` will contain only the compiled runtime and metadata — no source, tests, or `node_modules`.

```bash
npx --yes @vscode/vsce ls
```

Expected output (order may vary):

```text
README.md
package.json
CHANGELOG.md
out/backendRunner.js
out/contracts.js
out/extension.js
out/mrdEditorProvider.js
out/viewerController.js
out/webviewHtml.js
```

If you see `src/**`, `**/*.ts`, `out/test/**`, or `node_modules/**` in the list, fix `.vscodeignore` before packaging.

## 4. Package the Extension

```bash
npx --yes @vscode/vsce package
```

The `vscode:prepublish` script compiles the TypeScript first, then `vsce` writes the artifact. `vsce` prints a harmless `LICENSE ... not found` warning — the extension is licensed via the `"license": "MIT"` field in `package.json` and the repository-root [LICENSE](../../LICENSE) covers it. Expected result:

```text
DONE  Packaged: .../mrd-viz-0.0.1.vsix (11 files, ~18 KB)
```

The `.vsix` is git-ignored (see the repo `.gitignore`) and should **not** be committed; treat it as a build artifact (e.g. attach it to a GitHub Release).

## 5. Install the VSIX Locally

Windows PowerShell:

```powershell
code --install-extension mrd-viz-0.0.1.vsix
code --list-extensions --show-versions | Select-String "mrd-viz"
```

Linux / macOS Bash:

```bash
code --install-extension mrd-viz-0.0.1.vsix
code --list-extensions --show-versions | grep mrd-viz
```

Expected output:

```text
ismrmrd.mrd-viz@0.0.1
```

You can also install from the UI: **Extensions view → Views and More Actions (…) → Install from VSIX…**.

## 6. Set Up the Backend (Required to Open Files)

Installing the VSIX makes the extension available in every window, but rendering `.mrd` files needs the `mrd_viz` Python backend on the machine. The repo-relative `.venv` auto-detection only works when running from source (the F5 dev host) — an **installed** extension must be pointed at the interpreter explicitly via `mrdViz.pythonPath`.

You only need **steps 1–3** of the [Official Extension Development Runbook](OFFICIAL_EXT_DEV_RUNBOOK.md); they are reproduced here for convenience.

### 6a. Create the backend virtual environment (Python 3.12)

Windows PowerShell:

```powershell
$repoRoot = git rev-parse --show-toplevel
$backendRoot = Join-Path $repoRoot "mrd-viz/backend"
Set-Location $backendRoot
py -3.12 -m venv .venv
$python = Join-Path $backendRoot ".venv/Scripts/python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -e .
```

Linux / macOS Bash:

```bash
repo_root=$(git rev-parse --show-toplevel)
backend_root="$repo_root/mrd-viz/backend"
cd "$backend_root"
python3.12 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e .
```

### 6b. Confirm the interpreter path

Windows PowerShell:

```powershell
& $python -c "import sys, mrd_viz; print(sys.executable)"
```

Linux / macOS Bash:

```bash
./.venv/bin/python -c "import sys, mrd_viz; print(sys.executable)"
```

The printed path is the value you need next:

- Windows: `<repo-root>\mrd-viz\backend\.venv\Scripts\python.exe`
- Linux / macOS: `<repo-root>/mrd-viz/backend/.venv/bin/python`

### 6c. Point the extension at that interpreter

Set `mrdViz.pythonPath` to the path from 6b — via **Settings → search "mrdViz: Python Path"**, or in `settings.json`:

```json
{
  "mrdViz.pythonPath": "<repo-root>/mrd-viz/backend/.venv/bin/python"
}
```

> **Why set this explicitly?** If `mrdViz.pythonPath` is empty, the extension falls back to a bare `python` on `PATH`. On machines that only have `python3` (common on Linux/macOS), that lookup fails and you get a backend error even though Python is installed. Pointing `mrdViz.pythonPath` at the venv interpreter avoids the `python` vs `python3` ambiguity entirely.

> **Set this in User settings, not Workspace settings, if you also use the dev container.** A workspace `.vscode/settings.json` is bind-mounted into the dev container, so a host path set there (e.g. a Windows `...\.venv\Scripts\python.exe`) leaks into the container and overrides its Linux interpreter — producing a `spawn ... ENOENT` backend error. The dev container sets its own `mrdViz.pythonPath`; keeping the host value in **User** settings prevents the two from colliding.

### 6d. Open a file

Open any local `.mrd` file (double-click, or **MRD Viz: Open File** from the Command Palette). To generate test `.mrd` files, see section 4 of the [Official Extension Development Runbook](OFFICIAL_EXT_DEV_RUNBOOK.md).

### Optional: use the in-extension setup flow

Instead of manual step 6c, you can run **MRD Viz: Set Up Backend**:

- **Set up managed backend (recommended):** creates a managed virtual environment under extension global storage and installs `mrd-viz`.
- **Install backend from local wheel:** install from `mrd_viz-*.whl` (for example from a GitHub release bundle) and auto-configure `mrdViz.pythonPath`.

## 7. Update or Uninstall

Reinstalling a new build over an existing install:

```bash
npx --yes @vscode/vsce package
code --install-extension mrd-viz-0.0.1.vsix --force
```

Uninstall:

```bash
code --uninstall-extension ismrmrd.mrd-viz
```

## Notes

- **Publisher / icon:** `publisher` is set to `ismrmrd` so packaging succeeds; an `icon` is optional (only a warning). Both matter only when publishing to the Marketplace, which is out of scope for local installs.
- **Backend requirement:** installing the VSIX makes the extension available everywhere, but rendering still requires the `mrd_viz` Python backend and `mrdViz.pythonPath` pointed at its interpreter (section 6), whether by managed setup, local wheel, or manual provisioning.
- **Relation to publishing:** to later publish to the Marketplace, register the `ismrmrd` publisher and run `vsce publish`; the packaging config here (`.vscodeignore`, manifest metadata) is the same foundation.
