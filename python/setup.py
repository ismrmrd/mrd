import importlib.util
import os
from setuptools import setup

_spec = importlib.util.spec_from_file_location(
    'mrd._version',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mrd', '_version.py'),
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

setup(version=_mod.__version__)
