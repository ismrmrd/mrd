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
LICENSE
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

The `vscode:prepublish` script compiles the TypeScript first, then `vsce` writes the artifact. Expected result:

```text
DONE  Packaged: .../mrd-viz-0.0.1.vsix (12 files, ~18 KB)
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

## 6. Use It

Open any local `.mrd` file (double-click, or **MRD Viz: Open File** from the Command Palette). The extension needs the `mrd_viz` Python backend available — configure `mrdViz.pythonPath`, or rely on the local `mrd-viz/backend/.venv` fallback. See sections 2–5 of the [Official Extension Development Runbook](OFFICIAL_EXT_DEV_RUNBOOK.md) for backend setup and generating test `.mrd` files.

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
- **Backend requirement:** installing the VSIX makes the extension available everywhere, but rendering still requires the `mrd_viz` Python backend on the machine. Distributing the backend to end users is tracked separately.
- **Relation to publishing:** to later publish to the Marketplace, register the `ismrmrd` publisher and run `vsce publish`; the packaging config here (`.vscodeignore`, manifest metadata) is the same foundation.
