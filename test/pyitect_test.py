import os
import sys
folder_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(folder_path))

import pyitect
import json
cfgfile = open(os.path.join(folder_path, "config.json"))
cfg = json.load(cfgfile)
system = pyitect.System(cfg)
system.search(os.path.join(folder_path, "plugins"))
bar = system.load("bar")
bar()

for plugin, version in system.ittrPluginsByComponent("bar", {"test_plugin2": ">=0.0.1"}):
    print("%s:%s" % (plugin, version))