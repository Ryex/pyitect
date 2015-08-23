================
Creating Plugins
================

Contents:

.. toctree::
   :maxdepth: 4


What is a Plugin?
=================

A plugin to pyitect is simply a folder with a `.json` config file of the same
name as the folder inside.
If you have yaml support enabled the extensions `.yaml` and `.yml`
are also available

::

    /Im-A-Plugin
        Im-A-Plugin.json
        file.py

::

    /Im-A-Plugin2
        Im-A-Plugin2.yaml
        file.py

::

    /Im-A-Plugin3
        Im-A-Plugin3.yml
        file.py

A plugin has a name, a version, an author, a module or package, and it provides
Components used to build your application. a component is simply
an object which can be accessed from the imported module
a plugin's config file provides information about the plugin as well as
lists components it provides and components it needs on load

Here's an example, most fields are mandatory but the consumes and
provides CAN be left as empty containers

.. code-block:: json

    {
        "name": "Im-A-Plugin",
        "author": "author_name",
        "version": "0.0.1",
        "file": "file.py",
        "on_enable": "on_enable_func",
        "consumes": {
            "foo" : "*"
        },
        "provides": {
            "Bar": ""
        }
    }

Here is the same file in yaml

.. code-block:: yaml

    name: Im-A-Plugin
    author: author_name
    version: 0.0.1
    file: file.py
    on_enable: on_enable_func # optional, runs this function when the plugin is enabled
    consumes:
        foo: '*'
    provides:
        Bar: ''


Version numbers should conform to conformed to `Semantic Versioning <http://semver.org/>`_
meaning that they should have a major, minor, and patch number like so: `major.minor.patch-prereleace+buildifo`

-  **name** -> the name of the plugin (No spaces)
-  **author** -> the author of the plugin
-  **version** -> a version for the plugin, a string that conformes to `SemVer <http://semver.org/>`_
-  **file** -> a path to a function that will be called form the imported module after the plugin is loaded
-  **consumes** -> a mapping of needed component names to version requierments, empty string = no requirement
-  **provides** -> a mapping of provided component names to paths from the imported module, empty string = path is component name


Version Requirements
====================

A plugin can provide version requirements for the components it's
importing. they take two forms, a version string or a version mapping.

A version string is formatted like so

::

    plugin_name:<version_requirements>

Both parts are optional and an empty string or a string containing only
a `'*'` means no requirement.
If there is no requirement specified then the highest available version
will be selected from the first provider in alphabetical order.

if the version requirement is not give or given as * but the plugin name is
then the highest available version will be selected from the names plugin

A version requirement is a logical operator paired with a version number.
Any number of requirements can be grouped with commas.

Version numbers in requirements should also follow `Semantic Versioning <http://semver.org/>`_

Version requirement support is provided by the `python-semanticversion <https://github.com/rbarrois/python-semanticversion>`_ project.
specifically the `Spec` class. More documentation can be found `here <http://python-semanticversion.readthedocs.org/en/latest>`_.

Here are some examples of a version string

::

    ""  // no requirement
    "*" // no requirement
    "FooPlugin" // from this plugin and no other, but any version
    "FooPlugin:*" // from this plugin and no other, but any version
    "FooPlugin:==1" // from this plugin and no other, version 1.x.x
    "FooPlugin:==1.0" // 1.0.x
    "FooPlugin:==1.0.1" // version 1.0.1 or any post release
    "FooPlugin:==1.0.1-pre123" // 1.0.1-pre123 -> this exact version
    "FooPlugin:==1.2" // 1.2.x and any pre/post/dev release
    "FooPlugin:>1.0" // greater than 1.0
    "FooPlugin:>=1.2.3" // greater than or equal to 1.2.3
    "FooPlugin:<=2.1.4" // less than or equal to 2.1.4
    "FooPlugin:>1.0,<2.3" // greater than 1.0 and less than 2.3
    "FooPlugin:>1.0,<=2.0,!=1.3.17" // between V1.0.x and V2.0.x but not V1.3.17


Version requirements can also be given a a mapping.
The mapping must contain the keys `plugin` and `spec`
but this can allow for your requirement specification to be more clear.

Here is an example:

.. code-block:: json

    {
        "name": "Im-A-Plugin2",
        "author": "author_name",
        "version": "0.0.1",
        "file": "file.py",
        "consumes": {
            "foo" : {
                "plugin": "special_plugin_name",
                "spec": ">1.0,<=2.0,!=1.3.17"
            }
        },
        "provides": {
            "Bar": ""
        }
    }


The `spec` key can also be a list of version specifications

.. code-block:: json

    {
        "consumes": {
            "foo" : {
                "plugin": "special_plugin_name",
                "spec": [">1.0", "<=2.0,!=1.3.17"]
            }
        }
    }


Letting Plugins Access Consumed Components
==========================================


inside your plugin files you need to get access to your consumed
components right? Here's how you do it.

The plugin can pull it's declared components from :mod:`pyitect.imports`
during the import of the module or package.
:mod:`pyitect.imports` gets cleared after the import is done.
So, the component imports from :mod:`pyitect.imports`
should be in the top level of the module, not on demand imports in the code.

if a plugin author needs access to components not declared in the config file
for run time use - ie. to load component on the fly - then they will need the
system author to provide access to the plugin system instance.

Writing a Plugin
================

Writing a plugin for pyitect is simple.

*First*
    Create a folder to hold your plugin

*Second*
    Create a configuration file with the same name as the folder
    but with an extension. `.json` for a JSON config or `.yaml`/`.yml` for a YAML config

*Third*
    Create your python module or package. Your plugin folder can even be your package folder

*Forth*
    Write up your config for the plugin

    Point the file attribute to your module file or package.
    If it's a package point it to the `__init__.py`.
    It doesn't matter if your module is pure python, byte-code compiled (`.pyc`)
    or a native extension (`.pyd`, `.so`)


A working plugin looks something like the following:


Folder Structure

::

    /Im-A-Plugin
        Im-A-Plugin.json
        file.py

Im-A-Plugin.json

.. code-block:: json

    {
        "name": "plugin_name",
        "author": "author_name",
        "version": "0.1.0",
        "file": "<relative_path>",
        "on_enable": "<optional_function_path>",
        "consumes": {
            "foo" : "*"
        },
        "provides": {
            "Bar": ""
        }

file.py

.. code-block:: python

    #file.py
    from pyitect.imports import foo

    class Bar(object):
        def __init__():
            foo("it's a good day to be a plugin")
