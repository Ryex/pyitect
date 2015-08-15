import os
import json
import inspect
from nose import tools

import pyitect

folder_path = os.path.dirname(os.path.abspath(__file__))

system = None
pluginFoundTriggered = None
pluginLoadTriggered = None
componentLoadTriggered = None


def setup():
    # setup a plugin system
    global system

    cfgfile = open(os.path.join(folder_path, "config.json"))
    cfg = json.load(cfgfile)
    system = pyitect.System(cfg)

    system.bind_event('plugin_found', onPluginFound)
    system.bind_event('pluign_loaded', onPluginLoad)
    system.bind_event('component_loaded', onComponentLoad)

    print("\nSearching Plugin Path")
    system.search(os.path.join(folder_path, "plugins"))

    print("\nFiter out dead plugin before enableing plugins")
    plugins_filter = ["dead_plugin"]
    # get all plugin configs that arn't named dead_plugin
    # collect plugins[<name>][<version_str>] for all names n in plugins for all
    # versions v in plugins[n] if name not in filter
    plugins = [
        system.plugins[n][v]
        for n in system.plugins
        for v in system.plugins[n]
        if n not in plugins_filter
    ]

    print("\nEnableing plugins")
    system.enable_plugins(plugins)


def load_component(name):
    global system
    return system.load(name)


def onPluginFound(path, plugin):
    """
    path : the full path to the folder containing the plugin
    plugin : plugin version string (ie 'plugin_name:version')
    """
    global pluginFoundTriggered
    print("plugin `%s` found at `%s`" % (plugin, path))
    pluginFoundTriggered = True


def onPluginLoad(plugin, plugin_required, component_needed):
    """
    plugin : plugin version string (ie 'plugin_name:version')
    plugin_required: version string of the plugin that required the loaded
        plugin (version string ie 'plugin_name:version') (might be None)
    component_needed: the name of the component needed by the requesting plugin
    """
    global pluginLoadTriggered
    print(
        "plugin `%s` was loaded by plugin `%s` "
        "during a request for the `%s` component"
        % (plugin, plugin_required, component_needed)
    )
    pluginLoadTriggered = True


def onComponentLoad(component, plugin_required, plugin_loaded):
    """
    component : the name of the component loaded
    plugin_required : version string of the plugin that required the loaded
        component (version string ie 'plugin_name:version') (might be None)
    plugin_loaded : version string of the plugin that the component was loaded
        from (version string ie 'plugin_name:version')
    """
    global componentLoadTriggered
    print(
        "Component `%s` loaded, required by `%s`, loaded from `%s`"
        % (component, plugin_required, plugin_loaded)
    )
    componentLoadTriggered = True


def test_filter_plugins():
    global system
    tools.assert_true("dead_plugin" not in system.enabled_plugins)


def test_load_bar():
    global system
    bar = system.load("bar")
    tools.assert_true(inspect.isfunction(bar))


def test_component_version():
    global system
    versions = []
    compoents = []
    for plugin, version in system.ittrPluginsByComponent("test"):
        version_string = plugin + ":" + version

        tools.assert_true(version_string not in versions)

        versions.append(version_string)

        reqs = {"test": version_string}
        test = system.load("test", reqs)

        tools.assert_true(inspect.isfunction(test))
        tools.assert_true(test not in compoents)

        compoents.append(test)

def test_exec_import_relative():
    global system
    Exec_Foo_Echo_Relative = system.load("Exec_Foo_Echo_Relative")
    tools.assert_true(inspect.isfunction(Exec_Foo_Echo_Relative))


def test_relative_import():
    global system
    TestClass = system.load("TestClass")
    tools.assert_true(inspect.isclass(TestClass))


def test_fail_to_load_dead():
    tools.assert_raises(RuntimeError, load_component, "foobarbar")


def test_fetch_plugin_module():
    global system
    module = system.get_plugin_module("test_plugin")
    tools.assert_true(inspect.ismodule(module))


def test_on_enable_plugin():
    import sys
    tools.assert_true(hasattr(sys, "PYTITECT_TEST"))
