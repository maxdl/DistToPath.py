#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os.path import join, dirname

__version__ = __import__("disttopath.version").version

setup(
    name="DistToPath",
    version=__version__,
    description="Tool for analysis of immunogold labelling",
    long_description=open(join(dirname(__file__), "README.md")).read(),
    author="Max Larsson",
    author_email="max.larsson@liu.se",
    license="MIT",
    url="http://www.hu.liu.se/forskning/larsson-max/software",
    packages=find_packages(),
    entry_points={
    'console_scripts':
        ['DistToPath = disttopath.DistToPath:main']
    },
    install_requires=[
        'pyexcelerator'
    ]
)