from __future__ import (print_function)

import os
import sys
import json
import inspect
from pprint import pprint
from nose import tools

folder_path = os.path.dirname(os.path.abspath(__file__))

pyitect_path = os.path.dirname(folder_path)
sys.path.insert(0, pyitect_path)

import pyitect

system = None
pluginFoundTriggered = None
pluginLoadTriggered = None
componentLoadTriggered = None


def setup():
    # setup a plugin system
    global system
    global folder_path

    cfgfile = open(os.path.join(folder_path, "config.json"))
    cfg = json.load(cfgfile)
    system = pyitect.System(cfg, enable_yaml=True)


def test_01_bind_events():
    global system
    tools.ok_(not system.events)

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
        component_needed: the name of the component needed by the requesting
        plugin
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
        plugin_loaded : version string of the plugin that the component was
        loaded
            from (version string ie 'plugin_name:version')
        """
        global componentLoadTriggered
        print(
            "Component `%s` loaded, required by `%s`, loaded from `%s`"
            % (component, plugin_required, plugin_loaded)
            )
        componentLoadTriggered = True

    system.bind_event('plugin_found', onPluginFound)
    system.bind_event('plugin_loaded', onPluginLoad)
    system.bind_event('component_loaded', onComponentLoad)

    tools.ok_('plugin_found' in system.events)
    tools.ok_('plugin_loaded' in system.events)
    tools.ok_('component_loaded' in system.events)


def test_02_search_plugins():
    global system
    global folder_path

    tools.ok_(not system.plugins)

    system.search(os.path.join(folder_path, "plugins"))

    tools.ok_(len(system.plugins) > 0)


def test_03_enable_plugins():
    global system

    tools.ok_(not system.components)
    tools.ok_(not system.enabled_plugins)

    plugins_filter = ["bad_plugin"]
    # get all plugin configs that arn't named dead_plugin
    # collect plugins[<name>][<version_str>] for all names n in plugins for all
    # versions v in plugins[n] if name not in filter
    plugins = [
        system.plugins[n][v]
        for n in system.plugins
        for v in system.plugins[n]
        if n not in plugins_filter
        ]

    system.enable_plugins(plugins)

    tools.ok_(len(system.component_map) > 0)
    tools.ok_(len(system.enabled_plugins) > 0)


def test_04_filter_plugins():
    global system
    tools.ok_("bad_plugin" in system.plugins)
    tools.ok_("bad_plugin" not in system.enabled_plugins)


def test_05_fail_to_load_filtered():

    def load_component(name):
        global system
        return system.load(name)

    tools.assert_raises(
        pyitect.PyitectNotProvidedError,
        load_component,
        "foobarbar")


def test_06_provide_foo():
    global system
    foo = system.load("foo")
    tools.ok_(inspect.isfunction(foo))
    tools.eq_(foo(), "foo")


def test_07_provide_foov2():
    global system
    foo = system.load("foo", {"foo": "provide_plugin:==2.0.0"})
    tools.ok_(inspect.isfunction(foo))
    tools.eq_(foo(), "foo2")


def test_08_consume_foo():
    global system
    foobar = system.load("foobar")
    tools.ok_(inspect.isfunction(foobar))
    tools.eq_(foobar(), "foobar")


def test_09_components_subtypes():
    global system
    versions = []
    components = []

    subtypes = ("test.test1", "test.test2", "test.test3")
    for subtype in system.iter_component_subtypes("test"):
        tools.ok_(subtype in subtypes)
    for prov in system.iter_component_providers("test", subs=True):
        comp, plugin, version = prov
        version_string = comp + ":" + plugin + ":" + version

        tools.ok_(version_string not in versions)

        versions.append(version_string)

        test = system.load(comp)

        tools.ok_(inspect.isfunction(test))
        tools.ok_(test not in components)

        components.append(test)


def test_10_relative_import():
    global system
    TestClass = system.load("TestClass")
    tools.ok_(inspect.isclass(TestClass))
    T = TestClass("testmessage")
    tools.eq_(T.hello(), "testmessage")


def test_11_fetch_plugin_module():
    global system
    module = system.get_plugin_module("provide_plugin")
    tools.ok_(inspect.ismodule(module))


def test_12_on_enable_plugin():
    import sys
    tools.ok_(hasattr(sys, "PYTITECT_TEST"))


def test_13_yaml_plugin():
    global system
    foo_yaml = system.load("foo_yaml")
    tools.eq_(foo_yaml("testmessage"), "testmessageyaml")


def test_14_events_fired():
    global pluginFoundTriggered
    global pluginLoadTriggered
    global componentLoadTriggered

    tools.ok_(pluginFoundTriggered)
    tools.ok_(pluginLoadTriggered)
    tools.ok_(componentLoadTriggered)


def test_15_unique_module_names():
    global system

    TestClass = system.load("TestClass")

    print(TestClass.__module__)
    tools.assert_not_equal(
        TestClass.__module__, "relative_plugin.relative_test")


def test_16_bad_plugin_fails():
    global system

    def enable_plugin():
        global system
        system.load_plugin("bad_plugin", "0.0.1")

    tools.assert_raises(
        pyitect.PyitectLoadError,
        enable_plugin)

if __name__ == "__main__":
    setup()
    tests = []
    names = dict(globals())
    for name in names:
        if name[:4] == "test" and callable(names[name]):
            tests.append(name)
    for test in sorted(tests):
        print("Calling %s:" % (test,))
        names[test]()
