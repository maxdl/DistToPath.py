#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from os.path import join, dirname
from disttopath.version import version as __version__


setup(
    name="DistToPath",
    version=__version__,
    description="Tool for analysis of immunogold labelling",
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    author="Max Larsson",
    author_email="max.larsson@liu.se",
    license="MIT",
    url="http://www.hu.liu.se/forskning/larsson-max/software",
    packages=find_packages(),
    entry_points={
    'console_scripts':
        ['DistToPath = disttopath.DistToPath:main']
    },
    data_files=[('disttopath', ['disttopath/dtp.ico'])],
    install_requires=['pyexcelerator']    
    ]
)