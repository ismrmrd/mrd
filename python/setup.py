import os
from setuptools import setup

# Throw KeyError if MRD_VERSION_STRING is not set
version = os.environ['MRD_VERSION_STRING']

setup(version=version)
