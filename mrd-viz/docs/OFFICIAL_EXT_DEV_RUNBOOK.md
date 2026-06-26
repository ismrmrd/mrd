# Official Extension Development Runbook

Use these PowerShell steps from any local clone of the MRD repository to verify the MRD Viz backend, compile the VS Code extension, and launch an Extension Development Host.

These commands avoid machine-specific absolute paths. They derive paths from the Git repository root and use variables for local files such as sample MRD inputs.

For a backend-only CLI PR, sections 1 through 4 are the required verification path. Sections 5 through 9 cover extension development and extension-to-backend integration checks.

## 1. Open a Shell at the Repository Root

```powershell
Set-Location "<path-to-your-mrd-clone>"
$repoRoot = git rev-parse --show-toplevel
Set-Location $repoRoot
```

## 2. Create or Refresh the Backend Environment

```powershell
$backendRoot = Join-Path $repoRoot "mrd-viz/backend"
Set-Location $backendRoot

py -3.12 -m venv .venv
$python = Join-Path $backendRoot ".venv/Scripts/python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -e .
```

Expected result: the editable install completes without errors.

## 3. Verify the Backend Import Path

```powershell
& $python -c "import sys, mrd_viz; print(sys.executable); print(mrd_viz.__file__)"
```

Expected output should point to the backend virtual environment and source package inside this clone:

```text
<repo-root>\mrd-viz\backend\.venv\Scripts\python.exe
<repo-root>\mrd-viz\backend\src\mrd_viz\__init__.py
```

A `ModuleNotFoundError: No module named 'mrd_viz'` means the command is not using the backend virtual environment interpreter or the package has not been installed into that environment.

## 4. Run the Backend CLI Directly

Set `$sampleMrd` to a local MRD file that you want to inspect:

```powershell
$sampleMrd = Resolve-Path "<path-to-sample-mrd-file>"
& $python -m mrd_viz.cli open $sampleMrd --max-thumbnails 1
```

Expected result: JSON output on stdout. A successful response should include fields such as `ok`, `schema_version`, `file_class`, `display_mode`, `summary`, `stream`, and `mosaic`.

Optional CLI checks:

```powershell
& $python -m mrd_viz.cli classify $sampleMrd
& $python -m mrd_viz.cli image $sampleMrd --index 0
```

## 5. Compile the Extension

```powershell
$extensionRoot = Join-Path $repoRoot "mrd-viz/extension/mrd-viz"
Set-Location $extensionRoot

npm install
npm run compile
```

Expected result: `tsc -p ./` completes with no TypeScript errors.

## 6. Close Stale Development Hosts

Before relaunching, close every existing VS Code window titled `[Extension Development Host]`.

This matters because the extension JavaScript is loaded when the development host starts. If an old development host is still open, it can keep running stale compiled code.

## 7. Launch the Extension Development Host

From the extension folder:

```powershell
Set-Location $extensionRoot
code --new-window --extensionDevelopmentPath $extensionRoot
```

Expected result: VS Code opens a new window titled `[Extension Development Host]`.

If the development host opens on the Welcome page, use `File > Open Folder...` in that window and open the repository root:

```text
<repo-root>
```

## 8. Test the MRD Viz Command After Integration

This section applies after the extension contributes the MRD Viz open command and wires it to the backend CLI. Backend-only CLI PRs should stop after the direct CLI verification in section 4.

In the `[Extension Development Host]` window, run the MRD Viz command against the same sample MRD file used for backend CLI verification.

Open the `MRD Viz` output channel and confirm the command starts with the backend virtual environment interpreter:

```text
Running: <repo-root>\mrd-viz\backend\.venv\Scripts\python.exe -m mrd_viz.cli open ...
```

If the output starts with plain `python`, the development host is not running the current extension code or is not resolving the backend virtual environment fallback:

```text
Running: python -m mrd_viz.cli open ...
```

Fix that by closing all `[Extension Development Host]` windows, running `npm run compile` again from the extension folder, and relaunching the development host.

## 9. Optional F5 Workflow

Open this folder in the source VS Code window:

```text
<repo-root>\mrd-viz\extension\mrd-viz
```

In the Run and Debug view, select `Run Extension`, then press F5.

The same success check applies: the `MRD Viz` output channel should show the backend virtual environment Python path, not plain `python`.
