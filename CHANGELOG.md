v1.0.0
------
* change from parse_version from setuptools to LooseVersion in distutils
 
v0.9.2
------
* Ensure plugin configuration json file is closed @svisser

v0.9.1
------
* files loaded with `exec` give proper file path 
* proper trace back given when compoent fail to load (even when it's a recursion error) 
* add `component_mapped` event

v0.9.0
------
* add `get_plugin_module` method

v0.8.0
------
* Added ability to run code when a plugin is enabeled via `"on_enable"` property

v0.7.2
------
* Fix name error in unbind and fire event commands

v0.7.0
------
* plugins found with `System.search` are no longer auto enabeled
* use `System.enable_plugins(<mapping>|<iterable>|<Plugin>)` to enable plugins from `System.plugins`
* added `Plugin` class to main namespace

v0.6.2
------
* realative imports now work so long as the target file for loading is named `__init__.py` to triger python to treat the plugin folder as a package

v0.6.1
-----
* refactored System.load out to make use of two smaller functions, easyer to maintain
* added plugin loading modes, import for py3.4+ and exec for suport of prievious python version

v0.5.1
-----
* added ability to provide more than one version of a compoent in the same plugin with potfix mapping
* event system added, system fire events
* made requierment overwrite system defaults, removed bypass peram
* ittrPluginsByComponent lists potfix mappings too.
* tests updates to test all features
* README update
* This changelog added

v0.1.15
------
* added ittrPluginsByComponent
* added bypass peram to System.load to bypass system default

v0.1.10
------
* First public release
