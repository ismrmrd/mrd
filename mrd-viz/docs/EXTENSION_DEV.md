# Extension Development Runbook

Use these PowerShell steps to build the MRD Viz extension, launch an Extension Development Host window, and verify that the extension is using the backend virtual environment.

## 1. Verify the Backend Environment

```powershell
Set-Location "C:\Users\t-ccapetz\Documents\mrd\mrd-viz\backend"

.\.venv\Scripts\python.exe -c "import sys, mrd_viz; print(sys.executable); print(mrd_viz.__file__)"
```

Expected output should point to the backend venv and source package:

```text
C:\Users\t-ccapetz\Documents\mrd\mrd-viz\backend\.venv\Scripts\python.exe
C:\Users\t-ccapetz\Documents\mrd\mrd-viz\backend\src\mrd_viz\__init__.py
```

Run the backend CLI directly:

```powershell
.\.venv\Scripts\python.exe -m mrd_viz.cli open "C:\Users\t-ccapetz\Documents\mrd\mrd-viz\backend\src\mrd_viz\fastmri_knee_gt_RECON.mrd" --max-thumbnails 1
```

Expected result: JSON output. A `ModuleNotFoundError: No module named 'mrd_viz'` means the command is not using the backend venv interpreter.

## 2. Compile the Extension

```powershell
Set-Location "C:\Users\t-ccapetz\Documents\mrd\mrd-viz\extension\mrd-viz"

npm run compile
```

Expected result: `tsc -p ./` completes with no TypeScript errors.

## 3. Close Stale Development Hosts

Before relaunching, close every existing VS Code window titled `[Extension Development Host]`.

This matters because the extension JavaScript is loaded when the development host starts. If an old development host is still open, it can keep running stale compiled code.

## 4. Launch the Extension Development Host

From the extension folder:

```powershell
Set-Location "C:\Users\t-ccapetz\Documents\mrd\mrd-viz\extension\mrd-viz"

code --new-window --extensionDevelopmentPath "C:\Users\t-ccapetz\Documents\mrd\mrd-viz\extension\mrd-viz"
```

Expected result: VS Code opens a new window titled `[Extension Development Host]`.

If the development host opens on the Welcome page, use `File > Open Folder...` in that window and open:

```text
C:\Users\t-ccapetz\Documents\mrd
```

## 5. Test the MRD Viz Command

In the `[Extension Development Host]` window, run the MRD Viz command against:

```text
C:\Users\t-ccapetz\Documents\mrd\mrd-viz\backend\src\mrd_viz\fastmri_knee_gt_RECON.mrd
```

Open the `MRD Viz` output channel and confirm the command starts with the backend venv interpreter:

```text
Running: C:\Users\t-ccapetz\Documents\mrd\mrd-viz\backend\.venv\Scripts\python.exe -m mrd_viz.cli open ...
```

If the output starts with plain `python`, the development host is not running the current extension code or is not resolving the backend venv fallback:

```text
Running: python -m mrd_viz.cli open ...
```

Fix that by closing all `[Extension Development Host]` windows, running `npm run compile` again from the extension folder, and relaunching the development host.

## 6. Optional F5 Workflow

Open this folder in the source VS Code window:

```text
C:\Users\t-ccapetz\Documents\mrd\mrd-viz\extension\mrd-viz
```

In the Run and Debug view, select `Run Extension`, then press F5.

The same success check applies: the `MRD Viz` output channel should show the backend venv Python path, not plain `python`.