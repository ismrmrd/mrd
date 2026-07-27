"""PyInstaller entry point for the standalone mrd-viz backend binary.

Building this into a single self-contained executable lets the VS Code extension
ship a backend that needs no Python or PyPI on the user's machine.
"""

from mrd_viz.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
