**************
Useing Events
**************

The plugin system also includes a simple event system bound to the
:class:`system <pyitect.System>` object, it simply allows one to register
a function to an event name and when
:func:`system.fire_event <pyitect.System.fire_event>` is called it calls all
registered functions passing the extra `*args` and `**kwargs` to them.

pyitect fires some events internally so that you can keep track of when
the system finds and loads plugins.

Using Events
------------

Pyitect supplies three methods for dealing with events

:func:`System.bind_event <pyitect.System.bind_event>`


::

    system.bind_event('name', Function)

Binds `Function` to the event `'name'`. when an event of `'name'` is fired
the function will be called wall all extra parameters passed to the `fire_event` call.

:func:`System.unbind_event <pyitect.System.unbind_event>`

::

    system.unbind_event('name', Function)

Removes `Function` form the list of functions to be called when the event is fired

:func:`System.fire_event <pyitect.System.fire_event>`

::

    system.fire_event('name', *args, **kwargs)

Fires the event `'name'`, calling all bound functions with `*args` and `**kwargs`

Events Fired Internally
-----------------------


plugin\_found
=============


A function bound to this event gets called every time a plugin is found
during a search called an example is provided.

Example function to bind:

::

    def onPluginFound (path, plugin):
        """
        path (str): the full path to the folder containing the plugin
        plugin (str): plugin version string (ie 'plugin_name:version')
        """
        print("plugin `%s` found at `%s`" % (plugin, path))


component\_mapped
=================

When a plugin is enabled it's components are mapped out,
this event is fired ever time that happens.

Example function to bind:

::

    def onComponentMapped (component, plugin, version):
        """
        component (str): the component name
        plugin (str): plugin name
        version (Version): the plugin version string less the plugin name
        """
        print("component `%s` mapped form `%s@%s`" % (component, plugin, version))

plugin\_loaded
===============

A function bound to this event is called every time a new plugin is
loaded during a component load.

Example function to bind:

::

    def onPluginLoad (plugin, plugin_required, component_needed):
        """
        plugin (str): plugin version string (ie 'plugin_name:version')
        plugin_required (str): version string of the plugin that required the loaded plugin (version string ie 'plugin_name:version') (might be None)
        component_needed (str): the name of the component needed by the requesting plugin
        """
        print("plugin `%s` was loaded by plugin `%s` during a request for the `%s` component" % (plugin, plugin_required, component_needed))

component\_loaded
=================

A function bound to this event is called every time a component is
successfully loaded example:

Example function to bind:

::

    def onComponentLoad (component, plugin_required, plugin_loaded):
        """
        component (str): the name of the component loaded
        plugin_required (str): version string of the plugin that required the loaded component (version string ie 'plugin_name:version') (might be None)
        plugin_loaded (str): version string of the plugin that the component was loaded from (version string ie 'plugin_name:version')
        """
        print("Component `%s` loaded, required by `%s`, loaded from `%s`" % (component, plugin_required, plugin_loaded) )
