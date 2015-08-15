=======
Pyitect
=======

.. image:: https://travis-ci.org/Ryex/pyitect.svg?branch=master
    :target: https://travis-ci.org/Ryex/pyitect

A `architect <https://github.com/c9/architect>`_ inspired plugin
framework for Python 3 and Python >= 2.6

.. contents:: Table of Contents

*****************
What is a Plugin?
*****************


a plugin to pyitect is simply a folder with a .json file of the same
name inside

::

    /Im-A-Plugin
        Im-A-Plugin.json
        file.py

A plugin has a name, a version, an author, a module file, and it provides
Components used to build your application. components are simply names
in the module's namespace after the file is imported

a plugin's json file provides information about the plugin as well as
lists components it provides and components it needs on load

here's an example, all fields are mandatory but the consumes and
provides CAN be left as empty containers, but then the plugin would be
useless would it not? not providing components and all?

::

    {
        "name": "Im-A-Plugin",
        "author": "Ryex",
        "version": "0.0.1",
        "file": "file.py",
        "mode": "import", // optional either 'import' or 'exec'
        "on_enable": "dostuff.py", // optional, runs this file when the plugin is enabled
        "consumes": {
            "foo" : ""
        },
        "provides": {
            "Bar": ""
        }
    }

-  **name** -> the name of the plugin (No spaces)
-  **author** -> the author of the plugin
-  **version** -> a version for the plugin, a string that can be any form set up tools supports
-  **file** -> a path to the file that when imported will provide a module who's namespace contains all provided plugins
-  **mode** -> (OPTIONAL) defaults to `import` on python 3.4 and up `exec` otherwise: sets the import mode
-  **consumes** -> a mapping of needed component names to version strings, empty string = no requirement
-  **provides** -> a mapping of provided component names to prefix mappings

********************
Version Requirements
********************

a plugin can provide version requirements for the components it's
importing

a version string is formatted like so

::

    plugin_name:version_requirements

both parts are optional and an empty string or a string containing only
an '\*' means no requirement a version requirement can include logical
operators to get version greater than or less than the specified value,
you can evem select ranges

here are some examples

::

    ""  // no requirement
    "*" // no requirement
    "FooPlugin" // from this plugin and no other, but any version
    "FooPlugin:*" // from this plugin and no other, but any version
    "FooPlugin:1" // from this plugin and no other, version 1.x.x
    "FooPlugin:1.0" // 1.0.x
    "FooPlugin:1.0.1" // version 1.0.1 or any post release
    "FooPlugin:1.0.1-pre123" // 1.0.1-pre123 -> this exact version
    "FooPlugin:1.0.1.1" // oh did I mention that your version strings can basically go on forever? choose your own style!
    "FooPlugin:1.2" // 1.2.x and any pre/post/dev release
    "FooPlugin:>1.0" // greater than 1.0
    "FooPlugin:>=1.2.3" // greater than or equal to 1.2.3
    "FooPlugin:<=2.1.4" // less than or equal to 2.1.4
    "FooPlugin:>1.0 <2.3" // greater than 1.0 and less than 2.3
    "FooPlugin:1.0.5 - 2.4.5" // between 1.0.5 and 2.3.x inclusive
    "FooPlugin:1.0 || 2.5.1" // either 1.0.x or 2.5.1
    "FooPlugin:1.0 || 2.3.3 - 3.1.0 || >=4.3 <5.2.6-pre25" // get real complicated, cause you know, you might need it.

pyitect uses a reimplementation of the `LooseVersion` class's parse method (from the `version` module of `distutils`)
to parse versions. basically component of the version string are separated out, int casting is attempted,
and the components are then placed in a tulple

learn more from the `documentation <http://pydoc.org/2.5.1/distutils.version.html#LooseVersion>`_

the version parsing is available as a module level functions


Pyitect.parse_version(version_str):
-----------------------------------

dumbly parses a version string into it's parts
attempts to covert from string to integers where possible

Pyitect.gen_version(version_str):
-----------------------------------

generates an internally used version tuple
generates a 2 tuple
preserving the original version string in the first position
a parsed version in the second

******************************************
Letting plugins access consumed Components
******************************************


inside your plugin files you need to get access to your consumed
components right? here's how you do it

::

    #file.py
    from PyitectConsumes import foo

    class Bar(object):
        def __init__():
            foo("it's a good day to be a plugin")

**************************
Setting up a Plugin system
**************************


Here's how you set up a plugin system

::

    from pyitect import System
    #in case you need to specify versions for plugins that don't have a default
    #or you need to be sure a specific version is used,
    #you can supply a mapping of component names to version strings on system setup
    system = System({foo: "*"})

    system.search("path/to/your/plugins/tree")
    #enable the plugins found, you can of course do some filtering first
    plugins = [system.plugins[n][v] for n in system.plugins for v in system.plugins[n]]
    system.enable_plugins(plugins)

    Bar = system.load("Bar")

The general idea is to create a system, search some path or paths for plugins and then enable them
you can of course filter `System.plugins` in some way before passing it to `system.enable_plugins`

A plugin system can not be created without first creating an instance of the System class.

Enable Plugins
--------------


`System.enable_plugins()` accepts either a single `Plugin` object, a mapping object
where each key maps to a `Plugin` object, or an iterable (ie a list) of `Plugin` objects

Plugin components are not made available to the system until they are enabled.

'on_enable' Property
====================

plugins can specify an `on_enable` property in this configuration. This file is executed
right after a plugin is enabled and it's components have been mapped.
this allows for special cases where enabling a plugin requires more than just making it's components available to be imported.
for example is there is some system set up to be done.


Loading Plugins
---------------

Plugins are loaded on demand when a component is loaded via

::

    system.load("<component name>")

a plugin can also be explicitly loaded via

::

    system.load_plugin(plugin, version)

where `plugin` is the plugin name and `version` is the version

Plugin Loading Modes
====================

Plugins can be loaded in two different modes `import` and
`exec`. Both modes can be set in the plugin's json file just like
any other optional

import mode
^^^^^^^^^^^


`import` mode requires, and is the default on, Python version 3.4 or
higher. It uses the newly improved import lib to load the file pointed
to in the plugin json with the `file` property. This lets the file
to be loaded be any file python itself could import, be it a compiled
python module in `.pyd` or `.so` form, a `.pyc` or `.pyo`
compiled source file, or just a plain old `.py` source file.

exec mode
^^^^^^^^^


loads plugins by compiling the provided source file into a code object
and executing the code object inside a blank Module object. This
effectively recreates an import process by it's limited in that it can
only load raw python source not compiled `.pyc` or `.pyo` \_\_init
### both in both cases relative imports DO NOT WORK. the plugin folder
is temporarily added to the search path so absolute imports work but
relatives will not.

UNLESS the name of the file is `__init__.py` . In this special case
the plugin folder is reconsidered as a python package and relative
imports work as normal. exec mode does it's best to recognize this case
by testing for the file name `__init__.py` and then setting **name**
and **package** of the executed module to the folder name and
temporarily injecting the module into sys.modules.

Pyitect does it's best to isolate plugins from the rest of the program
by keeping clean namespaces but this is no substitute for good security
only load know plugins.


get_plugin_module
=================

Loaded plugins do NOT store their module object in `sys.modules`
instead they are stored internally at `System.loaded_plugins` (a mapping of plugin names and version strings to module objects)
Normaly you would only access a plugin's components but the module object can be accessed explicitly with

::

    system.get_plugin_module(plugin [, version=version_stirng])

if no version is given it fetches the highest version avalible.

a plugin must all ready be loaded (not just enabled) to fetch it's module object

Loading multiple versions of one component
------------------------------------------


There are times when you might want to load more than one version of a
plugin at once. why? well lets say you have a `tool` component that
does some function on a piece of data, what function? not important but
if you say wanted to extend the system to also allow an number of other
functions on that same data, perhaps some function provided by a 3d
party. how do make it so that all available functions are loaded?

Pyitect lets you classify all these as a single components with
different versions and then load them all.

::

    System.load(component, requirements={'component': 'plugin:version'})

in this case the requirements for the component can be set to load a
specific version from one plugin, bypassing the default from the system.

Tracking loaded Components
--------------------------

Pyitect tracks used components at anytime `System.using` can be
inspected to find all components that have been requested and from what
plugins they have been loaded along with versions `System.using` is
laying out as a multilayer dictionary with arrays of loaded versions,
here is an example where more than one version of a component is active

::

    >> System.using
    {
        'component1' : {
            'plugin1`: ['1.0.2']
        },
        'special_component1' : {
            'special_plugin1': ['0.1.3'],
            'special_plugin2': ['0.2.4', '1.0.1-pre3']
        }
    }


Pyitect also tracks enabled plugins `System.enabeled_plugins` is a mapping of plugin names to a mapping of
versions to `Plugin` objects. Like so

::

    >> System.enabeled_plugins
    {
        'special_plugin1' : {
            (0, 1, 3): Plugin<special_plugin1>
        }
    }


Providing multiple versions of a component from the same plugin
---------------------------------------------------------------


what if you want to provide multiple versions of a component from the
same plugin? if you have a system like in the Loading multiple versions
of one component section above then you may want to provide multiple
versions from one plugin

this can be accomplished by providing a version post-fix for the
provided component and map it to the Global name it can be accessed from
in the loaded module

you may of noticed that provided components are mapped to a string

::

    {
        "name": "Im-A-Plugin",
        ...
        "provides": {
            "Bar": ""
        }
    }

that string is a post-fix mapping, an empty string represent no mapping
(the component is provided in the loaded module under the same name, no
version post-fix)

if however we did this

::

    {
        "name": "Im-A-Plugin",
        ...
        "version": "0.0.1",
        ...
        "provides": {
            "Bar": "bar_type_1=bar1"
        }
    }

then a special version would be added to the system, version
`0.0.1-bar_type_1`, and when you required that version when loading
the `Bar` component it would load the name `bar1` from the module
loaded from the `Im-A-Plugin` plugin. More than one mapping can be
provided by separating them with the pipe `|` character in this way
more than one version can be provided. example:

::

    {
        "name": "Im-A-Plugin",
        ...
        "version": "0.0.1",
        ...
        "provides": {
            "Bar": "bar_type_1=bar1 | bar_type_2=bar2 | bar_type_3=bar3 | bar_type_4=bar4 | bar_type_5=bar5"
        }
    }

creating versions mappings
==========================

::

    0.0.1-bar_type_1 -> bar1
    0.0.1-bar_type_2 -> bar2
    0.0.1-bar_type_3 -> bar3
    0.0.1-bar_type_4 -> bar4
    0.0.1-bar_type_5 -> bar5

it is also possible to use the mapping to simple provide an alternate
name to acces the component under

::

    {
        "name": "Im-A-Plugin",
        ...
        "version": "0.0.1",
        ...
        "provides": {
            "FooBar": "=foobar",
            "BARFOO": "barfootype=barfoo"
        }
    }

notice that the version post-fix can be left out, as long as the `=`
is there the capitalized name `FooBar` can be accessed via the
lowercase name `foobar` but will still have the normal `0.0.1`
version

the second one `BARFOO` wil create a `0.0.1-barfootype` version.

*********************************
Usable method of the System class
*********************************

Static
------

There is only one Static class method

expand_version_requierment(version)
===================================

 Takes a string of one of the following forms:

::
    "" -> no version requierment
    "*" -> no version requierment
    "plugin_name" -> spesfic plugin no version requierment
    "plugin_name:version_ranges" -> plugin version matches requirements

and returns one of the following:

::
    ("", "") -> no version requierment
    ("plugin_name", "") -> plugin_name but no version requierment
    ("plugin_name", "verison_ranges")

Instance
--------

Once a `System` class in instantiated there are many methods that are usable


enable_plugins(plugins):
========================

enables one or more plugins

`plugins` is an iterable of Plugin class objects

search(self, path):
===================

search a path (dir or file) for plugins, in the case of a file it
searches the containing dir.

resolve_highest_match(component, plugin, version):
==================================================
resolves the latest version of a component with requirements,
passing empty strings means no requirements

in this case `plugin` is a name string and `version` is a version requirement string

::
    `version` Must match `version` exactly
    `>version` Must be greater than `version`
    `>=version` etc
    `<version`
    `<=version`
    `1.2` 1.2.0, 1.2.1, etc., but not 1.3.0
    `*` Matches any version
    "" (just an empty string) Same as *
    `version1 - version2` Same as `>=version1 <=version2`.
    `range1 || range2` Passes if either range1 or range2 are satisfied.

ittrPluginsByComponent(component, requirements=None):
=====================================================
iterates over the all possible providers of a component
returning the plugin name and the highest version possible.
if there are postfix version mappings for a component in a plugin
iterates over them too.

load_plugin(plugin, version, requesting=None, component=None):
==============================================================
`plugin` is a plugin name and `version` is a parsed version 2 tuple

requesting and component are strings used for events and errors. they should refer to the
'plugin@version' and 'component' that need the plugin loaded

takes a plugin name and version and finds the stored Plugin object
takes a Plugin object and loads the module
recursively loading declared dependencies

load(component, requires=None, requesting=None, bypass=False):
==============================================================
processes loading and returns the component by name,
chain loading any required plugins to obtain dependencies.
Uses the config that was provided on system creation
to load correct versions, if there is a conflict throws
a run time error.
bypass lets the call bypass the system configuration

get_plugin_module(plugin, version=None):
========================================
searches for the highest version number plugin with it's module loaded
if it can't find  it it raises a runtime error

******
Events
******

The plugin system also includes a simple event system bound to the
`system` object, it simply allows one to register a function to an
event name and when `system.fire_event` is called it calls all
registered functions passing the extra args and kwargs to them

pyitect fires some events internally so that you can keep track of when
the system finds and loads plugins

Using Events
------------

Pyitect supplies three methods for dealing with events

System.bind_event
=================
::

    system.bind_event('name', Function)

binds `Function` to the event `'name'`. when an event of `'name'` is fired
the function will be called wall all extra parameters passed to the `fire_event` call.

System.unbind_event
===================
::

    system.unbind_event('name', Function)

removes `Function` form the list of functions to be called when the event is fired

System.fire_event
=================
::

    system.fire_event('name', *args, **kwargs)

fires the event `'name'`, calling all bound functions with `*args` and `**kwargs`

Events Fired Internally
-----------------------


plugin\_found
=============


a function bound to this event gets called every time a plugin is found
during a search called an example is provided:

::

    def onPluginFound (path, plugin):
        """
        path : the full path to the folder containing the plugin
        plugin : plugin version string (ie 'plugin_name:version')
        """
        print("plugin `%s` found at `%s`" % (plugin, path))


component\_mapped
=================

when a plugin is enabled it's components are mapped out, this event is fired ever time that happens

::

    def onComponentMapped (component, plugin, version):
        """
        component : the component name
        plugin : plugin name
        version : the plugin version string less the plugin name
        """
        print("component `%s` mapped form `%s@%s`" % (component, plugin, version))

plugin\_loaded
===============-

a function bound to this event is called every time a new plugin is
loaded during a component load example:

::

    def onPluginLoad (plugin, plugin_required, component_needed):
        """
        plugin : plugin version string (ie 'plugin_name:version')
        plugin_required: version string of the plugin that required the loaded plugin (version string ie 'plugin_name:version') (might be None)
        component_needed: the name of the component needed by the requesting plugin
        """
        print("plugin `%s` was loaded by plugin `%s` during a request for the `%s` component" % (plugin, plugin_required, component_needed))

component\_loaded
=================

a function bound to this event is called every time a component is
successfully loaded example:

::

    def onComponentLoad (component, plugin_required, plugin_loaded):
        """
        component : the name of the component loaded
        plugin_required : version string of the plugin that required the loaded component (version string ie 'plugin_name:version') (might be None)
        plugin_loaded : version string of the plugin that the component was loaded from (version string ie 'plugin_name:version')
        """
        print("Component `%s` loaded, required by `%s`, loaded from `%s`" % (component, plugin_required, plugin_loaded) )


****************************************
Iterating over available plugin versions
****************************************


Pyitect provides an iterator function to iterate over available
providers for a component `System.ittrPluginsByComponent`

this function will loop over all plugin that provided the component and
return a tulple of the plugin name and it's highest available version.
if there are post-fix mappings for the component on that plugin it will
list them too.

::

    for plugin, version in system.ittrPluginsByComponent('component_name'):
        print("Plugin %s provides The component at version %s" % (plugin, version))

********
Examples
********


For more information checkout the tests directory, it should be a fairly
straight forward explanation form there.

*******
LICENSE
*******


Copyright (c) 2014, Benjamin "Ryex" Powers ryexander@gmail.com

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
