Pyitect
-------

A `architect <https://github.com/c9/architect>`__ inspired plugin
framework for Python 3.4+

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
            "foo" : "*"
        },
        "provides": [
            "Bar"
        ]
    }

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
    "FooPlugin:1.0.1.1" // oh did I not menchin that your version strings cna basicly go on forever? chouse your own style!
    "FooPlugin:1.2" // 1.2.x and any pre/post/dev releace
    "FooPlugin:>1.0" // greater than 1.0
    "FooPlugin:>=1.2.3" // greater than or equal to 1.2.3
    "FooPlugin:<=2.1.4" // less than or equal to 2.1.4
    "FooPlugin:>1.0 <2.3" // greater than 1.0 and less than 2.3
    "FooPlugin:1.0.5 - 2.4.5" // between 1.0.5 and 2.3.x inclusive
    "FooPlugin:1.0 || 2.5.1" // either 1.0.x or 2.5.1
    "FooPlugin:1.0 || 2.3.3 - 3.1.0 || >=4.3 <5.2.6-pre25" // get real complicated, cause you know, you might need it.

inside your plugin files you need to get acess to your consumed
components right? heres how you do it

::

    #file.py
    from PyitectConsumes import foo

    class Bar(object):
        def __init__():
            foo("it's a good day to be a plugin")
            

Here's how you set up a plugin system

::

    from pyitect import System
    #incase you need to spesify versions for plugins that dont have a default
    #or you need to besure a spesfic version is used, 
    #you can suply a mapping of compoent names to version strings on system setup
    system = System({foo: "*"}) 

    system.search("path/to/your/plugins/tree")

    Bar = system.load("Bar")

For more information checkout the tests directory, it sould be a farily
straite forward explination
