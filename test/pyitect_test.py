import os
import sys
from pprint import pprint
folder_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(folder_path))

def onPluginFound (path, plugin):
    """
    path : the full path to the folder containing the plugin
    plugin : plugin version string (ie 'plugin_name:version')
    """
    print("plugin `%s` found at `%s`" % (plugin, path))


def onPluginLoad (plugin, plugin_required, component_needed):
    """
    plugin : plugin version string (ie 'plugin_name:version')
    plugin_required: version string of the plugin that required the loaded plugin (version string ie 'plugin_name:version') (might be None)
    component_needed: the name of the component needed by the requesting plugin
    """
    print("plugin `%s` was loaded by plugin `%s` during a request for the `%s` component" % (plugin, plugin_required, component_needed))


def onComponentLoad (component, plugin_required, plugin_loaded):
    """
    component : the name of the component loaded
    plugin_required : version string of the plugin that required the loaded component (version string ie 'plugin_name:version') (might be None)
    plugin_loaded : version string of the plugin that the component was loaded from (version string ie 'plugin_name:version')
    """
    print("Component `%s` loaded, required by `%s`, loaded from `%s`" % (component, plugin_required, plugin_loaded) )

import pyitect
import json
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
# collect plugins[<name>][<version_str>] for all names n in plugins for all versions v in plugins[n] if name not in filter
plugins = [system.plugins[n][v] for n in system.plugins for v in system.plugins[n] if n not in plugins_filter]

pprint(plugins)

print("\nEnableing plugins")
system.enable_plugins(plugins)

print("\nLoading `bar` component")
bar = system.load("bar")
bar()

print("\nIterating component providers")
for plugin, version in system.ittrPluginsByComponent("test"):
    print("Plugin `%s` provides The component at version `%s`" % (plugin, version))
    version_string = plugin + ":" + version
    print(version_string)
    reqs = { "test" : version_string }
    test = system.load("test", reqs)
    print("\ncalling test")
    test()
    print("\n")

print("\nImporting plugin via 'exec'")
Exec_Foo_Echo = system.load("Exec_Foo_Echo")
Exec_Foo_Echo("I am being echoed back by a plugin loaded via exec")

Exec_Foo_Echo_Relative = system.load("Exec_Foo_Echo_Relative")
Exec_Foo_Echo_Relative("This text should be printed by a absolute import method")

print("\nImporting relative import test plugin")
TestClass = system.load("TestClass")
t = TestClass("relative imports were a success")
t.hello()

print("\nAttempt to import dead plugin")

try:
    foobarbar = system.load("foobarbar")
    foobarbar()
except RuntimeError as err:
    print("\ndead_plugin failed to load, this is intended")
    
print("\nTest fetching plugin module")

module = system.get_plugin_module("test_plugin")

pprint(module.__dict__)