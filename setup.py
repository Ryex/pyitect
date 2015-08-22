#!/usr/bin/python3
from setuptools import setup, find_packages
import os

local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return None


def clean_readme(fname):
    """Cleanup README.rst for proper PyPI formatting."""
    with codecs.open(fname, 'r', 'utf-8') as f:
        return ''.join(
            re.sub(r':\w+:`([^`]+?)( <[^<>]+>)?`', r'``\1``', line)
            for line in f
            if not (line.startswith('.. currentmodule')
                    or line.startswith('.. toctree')))

PACKAGE = 'pyitect'

setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    packages=find_packages(),
    install_requires=["setuptools >= 1.0"],
    include_package_data=True,
    # metadata for upload to PyPI
    author='Benjamin "Ryex" Powers',
    author_email="Ryexander+pyitect@gmail.com",
    description=(
        "A simple system for structuring a modeler project "
        "architecture via plugin like modules, uses the new "
        "importlib abilities first avalible in python 3.4, "
        "includes an exec load mode for support of python 3.0+"),
    long_description=local_file("README.rst"),
    license="ISC",
    keywords=["architect", "project", "modeler", "module", "plugin"],
    url="https://github.com/Ryex/pyitect",
    download_url='https://pypi.python.org/pypi/pyitect/',
    install_requires=[
        "semantic_version>=2.4.2"
    ]
    tests_require=[
        "nose",
        "pyyaml"
        ],
    extras_require = {
        'yaml': 'pyyaml'
        },
    test_suite='nose.collector',

    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
        ]
    )
