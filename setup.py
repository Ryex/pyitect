#!/usr/bin/python3
from setuptools import setup, find_packages
import os

local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()


setup(
    name="pyitect",
    version="1.1.0",
    packages=find_packages(),
    install_requires=["setuptools >= 1.0"],
    include_package_data=True,
    # metadata for upload to PyPI
    author="Ryexander",
    author_email="Ryexander@gmail.com",
    description=(
        "A simple system for structuring a modeler project "
        "architecture via plugin like modules, uses the new "
        "importlib abilities first avalible in python 3.4, "
        "includes an exec load mode for support of python 3.0+"),
    long_description=local_file("README.rst"),
    license="ISC",
    keywords="architect project modeler plugin",
    url="https://github.com/Ryex/pyitect",
    tests_require=[
        "nose"
    ],
    test_suite='nose.collector',

    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",

        "License :: OSI Approved :: ISC License (ISCL)",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ]
)
