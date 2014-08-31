from setuptools import setup, find_packages
import os

local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()
    
try:
    from pypandoc import convert
    output = convert("README.md", 'rst')
    readme_rst = open("README.rst", "w")
    readme_rst.write(output)
    readme_rst.close()
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")


setup(
    name = "pyitect",
    version = "0.5.1",
    packages = find_packages(exclude=['*test*']),
    install_requires=["setuptools >= 1.0"],
    include_package_data=True,
    # metadata for upload to PyPI
    author = "Ryexander",
    author_email = "Ryexander@gmail.com",
    description = """A Simple system for structuring a modeler project architecture via plugin like modules, uses the new importlib abilities first avalible in python 3.4""",
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