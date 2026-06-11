import importlib.util
import os
from setuptools import setup

_spec = importlib.util.spec_from_file_location(
    'mrd._version',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mrd', '_version.py'),
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Failed to load python/mrd/_version.py for package version")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

setup(version=_mod.__version__)
