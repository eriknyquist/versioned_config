import unittest
import os
import sys
from setuptools import setup, find_packages

from versioned_config import __version__ as version

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

with open(README, 'r') as f:
    long_description = f.read()

setup(
    name='versioned_config',
    version=version,
    description=('library for creating and managing versioned configuration files'),
    long_description=long_description,
    url='http://github.com/eriknyquist/versioned_config',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    packages=find_packages(),
)
