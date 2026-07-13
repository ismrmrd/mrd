# PyInstaller spec for the standalone mrd-viz backend binary.
#
# Build (from mrd-viz/backend):
#   python -m pip install ".[package]"
#   pyinstaller --clean --noconfirm packaging/mrd-viz.spec
#
# Produces a one-dir bundle at dist/mrd-viz/ (dist/mrd-viz/mrd-viz[.exe] plus an
# _internal/ folder of libraries). A one-DIR (not one-file) build is deliberate:
# one-file extracts python3xx.dll to a temp dir at runtime, which Windows
# Application Control blocks on managed machines. Keeping the DLLs next to the
# executable runs without code signing. The extension's resolver looks for the
# executable at media/backend/mrd-viz[.exe] inside the VSIX.
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
    [],
    exclude_binaries=True,
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

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="mrd-viz",
)
