v0.6.2
------
realative imports now work so long as the target file for loading is named `__init__.py` to triger python to treat the plugin folder as a package

v0.6.1
-----
refactored System.load out to make use of two smaller functions, easyer to maintain
added plugin loading modes, import for py3.4+ and exec for suport of prievious python version

v0.5.1
-----
added ability to provide more than one version of a compoent in the same plugin with potfix mapping
event system added, system fire events
made requierment overwrite system defaults, removed bypass peram
ittrPluginsByComponent lists potfix mappings too.
tests updates to test all features
README update
This changelog added

v0.1.15
------
added ittrPluginsByComponent
added bypass peram to System.load to bypass system default

v0.1.10
------
First public release