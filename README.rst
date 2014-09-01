Pyitect
=======

A `architect <https://github.com/c9/architect>`__ inspired plugin
framework for Python 3.4+ (3.4+ is required because of the use of the
new import lib abilities)

What is a Plugin?
-----------------

a plugin to pyitect is simply a folder with a .json file of the same
name inside

::

    /Im-A-Plugin
        Im-A-Plugin.json
        file.py

A plugin has a name, a version, an author, a .py file, and it provides
Components used to build your aplication. components are simply names in
the module's namespace after the file is imported

a plugin's json file provides information about the plugin as well as
lists components it provides and components it needs on load

here's an example, all feilds are manditory but the consumes and
provides CAN be left as empty containers, but then the plugin would be
useless would it not? not providing components and all?

::

    {
        "name": "Im-A-Plugin",
        "author": "Ryex",
        "version": "0.0.1",
        "file" : "file.py",
        "consumes": {
            "foo" : ""
        },
        "provides": {
            "Bar": ""
        }
    }

Version Requierments
--------------------

a plugin can provid version requierments for the components it's
importing

a version string is formated like so

::

    plugin_name:version_requierments

both parts are optional and an empty stirng or a string contaiing only
an '\*' means no requierment a version requierment can include logical
operators to get version greater than or less than the spesifiyed value,
you can evem select ranges

here are some examples

::

    ""  // no requierment
    "*" // no requierment
    "FooPlugin" // from this plugin and no other, but any version
    "FooPlugin:*" // from this plugin and no other, but any version
    "FooPlugin:1" // from this plugin and no other, verison 1.x.x
    "FooPlugin:1.0" // 1.0.x
    "FooPlugin:1.0.1" // version 1.0.1 or any post releace
    "FooPlugin:1.0.1-pre123" // 1.0.1-pre123 -> this exact version
    "FooPlugin:1.0.1.1" // oh did I mention that your version strings can basicly go on forever? chouse your own style!
    "FooPlugin:1.2" // 1.2.x and any pre/post/dev releace
    "FooPlugin:>1.0" // greater than 1.0
    "FooPlugin:>=1.2.3" // greater than or equal to 1.2.3
    "FooPlugin:<=2.1.4" // less than or equal to 2.1.4
    "FooPlugin:>1.0 <2.3" // greater than 1.0 and less than 2.3
    "FooPlugin:1.0.5 - 2.4.5" // between 1.0.5 and 2.3.x inclusive
    "FooPlugin:1.0 || 2.5.1" // either 1.0.x or 2.5.1
    "FooPlugin:1.0 || 2.3.3 - 3.1.0 || >=4.3 <5.2.6-pre25" // get real complicated, cause you know, you might need it.

pyitect uses ``parse_version`` from the ``pkg_resources`` module (part
of setuptools) to turn version strings into tuples that are then
compaired lexagraphicaly so any version string system that works with
setuptools works here

learn more from the `parse\_version
docs <https://pythonhosted.org/setuptools/pkg_resources.html#id33>`__

Letting plugins access consumed Components
------------------------------------------

inside your plugin files you need to get acess to your consumed
components right? heres how you do it

::

    #file.py
    from PyitectConsumes import foo

    class Bar(object):
        def __init__():
            foo("it's a good day to be a plugin")

Setting up a Plugin system
--------------------------

Here's how you set up a plugin system

::

    from pyitect import System
    #incase you need to spesify versions for plugins that dont have a default
    #or you need to besure a spesfic version is used,
    #you can suply a mapping of component names to version strings on system setup
    system = System({foo: "*"})

    system.search("path/to/your/plugins/tree")

    Bar = system.load("Bar")

Loading multiple versions of one component
------------------------------------------

There are times when you might want to load more than one version of a
plugin at once. why? well lets say you have a ``tool`` component that
does some function on a piece of data, what function? not important but
if you say wanted to extend the system to also allow an number of other
functions on that same data, perhaps some function provided by a 3d
party. how do make it so that all avalible functions are loaded?

Pyitect lets you classify all these as a single components with
different versions and then load them all.

::

    System.load(component, requierments={'component': 'plugin:version'})

in this case the requierments for the component can be set to load a
spesfic version from one plugin, bypassing the default from the system.

Tracking loaded Components
--------------------------

Pyitect tracks used components at anytime ``System.useing`` can be
inspected to find all components that have been requested and from what
plugins they have been loaded along with versions ``System.useing`` is
laying out as a multilayer dictionary with arrays of loaded versions,
here is an example where more than one version of a component is active

::

    >> System.useing
    {
        'component1' : {
            'plugin1`: ['1.0.2']
        },
        'special_component1' : {
            'special_plugin1': ['0.1.3'],
            'special_plugin2': ['0.2.4', '1.0.1-pre3']
        }
    }

Events
------

The plugin system also includes a simple event system bount to the
``System`` object, it simply allows one to register a function to an
event name and when ``System.fire_event`` is called it calls all
registered functions passing the extra args and kwargs to them

pyitect fires some event internaly so that you can keep track of when
the system finds and loads plugins

'plugin\_found'
^^^^^^^^^^^^^^^

a function bound to this event gets called every time a plugin is found
during a search called an example is provided:

::

    def onPluginFound (path, plugin):
        """
        path : the full path to the folder containing the plugin
        plugin : plugin version string (ie 'plugin_name:version')
        """
        print("plugin `%s` found at `%s`" % (plugin, path))

'plugin\_loaded'
^^^^^^^^^^^^^^^^

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

'component\_loaded'
^^^^^^^^^^^^^^^^^^^

a function bound to this event is called every time a component is
sucessfuly loaded example:

::

    def onComponentLoad (component, plugin_required, plugin_loaded):
        """
        component : the name of the component loaded
        plugin_required : version string of the plugin that required the loaded component (version string ie 'plugin_name:version') (might be None)
        plugin_loaded : version string of the plugin that the component was loaded from (version string ie 'plugin_name:version')
        """
        print("Component `%s` loaded, required by `%s`, loaded from `%s`" % (component, plugin_required, plugin_loaded) )

Providing multiple versions of a component from the same plugin
---------------------------------------------------------------

what if you want to provide multiple versions of a component from the
same plugin? if you have a system like in the Loading multiple versions
of one component section above then you may want to provide multiple
versions from one plugin

this can be acomplished by providing a version postfix for the provided
component and map it to the Global name it can be accesed from in the
loaded module

you may of noticed that provided components are mapped to a string

::

    {
        "name": "Im-A-Plugin",
        ...
        "provides": {
            "Bar": ""
        }
    }

that string is a postfix mapping, an empty string represent no mapping
(the component is provided in the loaded module under the same name, no
version postfix)

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

then a special version would be added to the system, verison
``0.0.1-bar_type_1``, and when you required that version when loading
the ``Bar`` component it would load the name ``bar1`` from the module
loaded from the ``Im-A-Plugin`` plugin. More than one mapping can be
provided by sperating them with teh pipe ``|`` charater in this way more
than one version can be provided. example:

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

creating versions mapings

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

notice that the version postfix can be left out, as long as the ``=`` is
there the capitalized name ``FooBar`` can be accessed via the lowercase
name ``foobar`` but will still have the normal ``0.0.1`` version

the second one ``BARFOO`` wil create a ``0.0.1-barfootype`` version.

Iterating over avalible plugin versions
---------------------------------------

Pyitect provides an iterator function to iterate over avalible providers
for a component ``System.ittrPluginsByComponent``

this function will loop over all pluign that provided the component and
return a tulple of the plugin name and it's highest avalible version. if
there are postfix mappings for the component on that plugin it will list
them too.

::

    for plugin, version in System.ittrPluginsByComponent('component_name'):
        print("Plugin %s provides The component at version %s" % (plugin, version))

Examples
--------

For more information checkout the tests directory, it sould be a farily
straight forward explination form there.

LICENSE
-------

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
