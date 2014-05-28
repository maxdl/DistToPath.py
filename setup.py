#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os.path import join, dirname

PACKAGE = "disttopath"
NAME = "DistToPath"
DESCRIPTION = ""
AUTHOR = "Max Larsson"
AUTHOR_EMAIL = "max.larsson@liu.se"
URL = "http://www.hu.liu.se/forskning/larsson-max/software"
VERSION = __import__(PACKAGE).__version__

setup(
    name="DistToPath",
    version=__import__(PACKAGE).__version__,
    description="Tool for analysis of immunogold labelling",
    long_description=open(join(dirname(__file__), "README.md")).read(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
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