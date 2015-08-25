Setting up a Plugin system
==========================

Setting up a plugin system is dead simple.

First create an instance of the :class:`System <pyitect.System>` class

::

    from pyitect import System
    system = System()

The system class constructor takes two arguments,
a configuration mapping and a `yaml` flag

The config mapping allows you to provide default requirements for components
so if a call is made to :func:`system.load() <pyitect.System.load>`
with no requirements of it's own the requirements from the
passed config are used.

The `yaml` flag of course enables `yaml` support for the plugin system.
allowing configuration file to be written in yaml. `yaml` support is not
enabled by default because it requires the `PyYAML <http://pyyaml.org/>`_
library.

Next add some plugins to the system.

This can be done either by using the :func:`system.search() <pyitect.System.search>`
function to recursively search a directory for plugins.

Or added manualy by providing the path to a plugin folder to the
:func:`system.add_plugin() <pyitect.System.add_plugin>` function of your system
instance.

::

    system.search("path/to/your/plugins/tree")
    system.add_plugin("paht/to/a/plugin/folder")


Now that you have some plugin you still have to enable them.

Enabling a plugin maps out the components it provides and make them available
for loading by the plugin system. Tt does not load the plugin module or package
unless there is an 'on_enable` property in its configuration.

In which case, after the component are mapped and the plugin is enabled,
the plugin module or package is loaded
and an attempt is made to follow the path given to the `on_enable`
configuration property to a callable object (ie. function) from the top level
of the module or package and it is called
passing only the :class:`Plugin <pyitect.Plugin>` configuration object for the
plugin.

To enable a plugin you needs it's :class:`Plugin <pyitect.Plugin>` instance.
these can be accessed from :attr:`system.plugins <pyitect.System.plugins>`

a simple way to get a list of them would be.

::

    plugins = [system.plugins[n][v] for n in system.plugins for v in system.plugins[n]]


After you have your list of Plugin objects you can filer it how you want
to enable only the plugins you want to. When your ready.

::

    system.enable_plugins(plugins)


`enable_plugins` can take multiple objects and any individual
 can by a iterable or map of :class:`Plugin <pyitect.Plugin>` objects.

After you have some plugins enabled loading a provided component is as easy as

::

    Bar = system.load("Bar")


The general idea is to create a system, search some path or paths for plugins
and then enable them.


A plugin system can not be created without first creating an
instance of the System class.


Global System
--------------

If you dont want to manage your plugin system instance yourself
it is possible to have the pyitect module manage your plugin system for you.
Simply use the :func:`pyitect.build_system` function to construct your
plugin system inside pyitect. To later fetch your plugin system instance use
:func:`pyitect.get_system`. To clean up and remove the existing system use
:func:`pyitect.destroy_system`.


'on_enable' Property
--------------------

plugins can specify an :attr:`on_enable <pyitect.Plugin.on_enable>`
property in their configuration. This is a doted name path to a function
that is is executed right after a plugin is enabled and
its components have been mapped. This allows for special cases where enabling
a plugin requires more than just making it's components available
to be imported. For example is there is some system setup to be done.

::

    pyitect.build_system(config, enable_yaml=False)
    system = pyitect.get_system()
    # ... do stuff
    # end program / need fresh system?
    pyitect.destroy_system()

Loading Components at run-time
------------------------------

Components are loaded at runtime via the
:meth:`system.load <pyitect.System.load>` method or the
:meth:`system.load_component <pyitect.System.load_component>` method

the second method requires you to explicitly state a plugin a version to load
from this is not a common use can and is intended mostly for use with
:meth:`system.iter_component_providers <pyitect.System.iter_component_providers>`.

The first method only needs the name of a component and will load any matching
provider even if it is a subtype. This is the most common usecase

::

    # if "a" is not avalieable will also load a "a.b" or "a.c"
    a = system.load("a")

If the subtype matching is undesirable then it can be explicitly prevented with
a key word argument

::

    # will only load a "a" not a "a.b"
    a = system.load("a", subs=False)

The default mode for selecting form among subtype is to sort alphanumerically
and pick the first one. This is often not a desirable behavior in more complex
situations. As such a `key` peramiter can be used

::

    def key(prov):
        return (0 if prov[0] == "a.b" else 1)

    # results in the loading of an "a.b"
    a = system.load("a", key=key)

your key function cna be as complex or as simple as you want. they are sorting
the results of a call to :meth:`system.iter_component_providers <pyitect.System.iter_component_providers>`.
which yeilds tuples that look like `(<component_name>, <plugin_name>, <version>)`

if nessaccery there is a reverse kework perams to reverse the results of the sort

::

    # results in the load of the logest and highest subtype
    a = system.load("a", reverse=True)



Loading Plugins
---------------

Plugins are loaded on demand when a component is loaded via

::

    system.load("<component name>")


a plugin can also be explicitly loaded via

::

    system.load_plugin(plugin, version)


where `plugin` is the plugin name and `version` is the version

Tracking loaded Components
--------------------------

Pyitect tracks used components at anytime
:attr:`system.using <pyitect.System.using>` can be
inspected to find all components that have been requested and from what
plugins they have been loaded along with versions.

:attr:`system.using <pyitect.System.using>` is a list of
:func:`component.key() <pyitect.Component.key>` s

::

    >>> system.using
    {
        'component1' : {
            'plugin1`: ['1.0.2']
        },
        'special_component1' : {
            'special_plugin1': ['0.1.3'],
            'special_plugin2': ['0.2.4', '1.0.1-pre3']
        }
    }


Pyitect also tracks enabled plugins
:attr:`system.enabeled_plugins <pyitect.System.enabeled_plugins>`
is a mapping of plugin names to a mapping of versions to
:class:`Plugin <pyitect.Plugin>` objects.

Like so

::

    >>> system.enabeled_plugins
    {
        "special_plugin1" : {
            "Version('1.0.0')": Plugin('special_plugin1:1.0.0')
        }
    }
