# PyInstaller spec for the standalone mrd-viz backend binary.
#
# Build (from mrd-viz/backend):
#   python -m pip install . pyinstaller
#   pyinstaller --clean --noconfirm packaging/mrd-viz.spec
#
# Produces dist/mrd-viz (dist/mrd-viz.exe on Windows). The extension's backend
# resolver looks for this at media/backend/mrd-viz[.exe] inside the VSIX.
#
# NOTE: numpy and pillow are covered by PyInstaller's bundled hooks. mrd-python
# (imported as `mrd`) is collected explicitly below; if a submodule is missed at
# runtime, add it to `hiddenimports`.

from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules("mrd") + collect_submodules("mrd_viz")

analysis = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="mrd-viz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
