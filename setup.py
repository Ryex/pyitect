from setuptools import setup, find_packages
import os

local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()

setup(
    name = "pyitect",
    version = "0.1.15",
    packages = find_packages(exclude=['*test*']),
    install_requires=["setuptools >= 1.0"],
    include_package_data=True,
    # metadata for upload to PyPI
    author = "Ryexander",
    author_email = "Ryexander@gmail.com",
    description = "A package for structuring a modeler project architecture via plugin like modules",
    long_description = local_file("README.rst"),
    license = "ISC",
    keywords = "architect project modeler plugin",
    url = "https://github.com/Ryex/pyitect",
    tests_require = [
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
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