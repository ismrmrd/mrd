import os
from datetime import date
from setuptools import setup

version = os.getenv('MRD_VERSION_STRING', date.today().strftime('%Y.%m.%d'))

setup(version=version)
