import importlib.util
import json
import sys
import os
import types
import collections
import re
import warnings
import operator


class Plugin(object):

    """
    an object that can hold the metadata for a plugin,
    like its name, author, verison, and the file to be loaded ect.


    properties:
    name - plugin name
    author - plugin author
    version - pluing vesion
    file - the file to import to load the plugin
    consumes - a listing of the components consumed
    provides - a listing of the components provided

    """

    def __init__(self, config, path):
        """
        init the plugin container object and pull information from it's passed
        config, storing the path where it can be found
        """
        if 'name' in config:
            self.name = config['name'].strip()
        else:
            raise RuntimeError(
                "Plugin as '%s' does not have a name string" % path)
        if 'author' in config and isinstance(config['author'], str):
            self.author = config['author'].strip()
        else:
            raise RuntimeError(
                "Plugin as '%s' does not have a author string" % path)
        if 'version' in config:
            # store both the original version string and a parsed version that
            # can be compaired accurately
            self.version = (
                config['version'].strip(),
                parse_version(config['version'].strip())
            )
        else:
            raise RuntimeError("Plugin at '%s' does not have a version" % path)
        if 'file' in config:
            self.file = config['file'].strip()
        else:
            raise RuntimeError(
                "Plugin as '%s' does not have a plugin file spesified" % path)
        if (('consumes' in config) and
                isinstance(config['consumes'], collections.Mapping)):
            self.consumes = config['consumes']
        else:
            raise RuntimeError(
                "Plugin at '%s' has no map of consumed "
                "components to plugin versions" % path)
        if (('provides' in config) and
                isinstance(config['provides'], collections.Mapping)):
            self.provides = config['provides']
        else:
            raise RuntimeError(
                "Plugin at '%s' hs no map of provided components"
                " to version postfixes" % path)
        if (('mode' in config) and
                ((config['mode'].lower() == 'import') or
                    (config['mode'] == 'exec'))):
            self.mode = config['mode']
            if self.mode == 'import' and not Plugin.supports_import_mode():
                self.mode = 'exec'
                warnings.warn(RuntimeWarning(
                    "Plugin at '%s' has set 'import' mode but this mode is "
                    "only suported in python 3.4 and up:"
                    "\ndefaulting to 'exec' mode" % path))
        elif not ('mode' in config):
            self.mode = 'import' if Plugin.supports_import_mode() else 'exec'
        else:
            raise RuntimeError(
                "Plugin at '%s' has bad mode, 'import' and 'exec' allowed"
                % path)
        if 'on_enable' in config:
            if isinstance(config['on_enable'], str):
                self.on_enable = config['on_enable']
            else:
                raise RuntimeError(
                    "Plugin at '%s' has a 'on_enable' that is not a string"
                    % path)
        else:
            self.on_enable = None
        self.path = path

    @staticmethod
    def supports_import_mode():
        return sys.hexversion >= 0x030400F0

    def _load_import(self):
        # import can handle cases where the file isn't a python source file,
        # for example a compiled pyhton module in the form of a .pyd or .so
        # only works with pyhton 3.4+
        filepath = os.path.join(self.path, self.file)
        try:
            sys.path.insert(0, self.path)
            spec = importlib.util.spec_from_file_location(self.name, filepath)
            plugin = spec.loader.load_module()
            sys.path.remove(self.path)
        except Exception as err:
            raise RuntimeError(
                "Plugin '%s' at '%s' failed to load" % (self.name, self.path)
            ) from err

        return plugin

    def _load_exec(self):
        filepath = os.path.join(self.path, self.file)
        module_name = os.path.splitext(self.file)[0]
        # exec mode requieres the file to be raw python
        package = False
        if module_name == '__init__':
            module_name = os.path.basename(self.path)
            package = True
        try:
            plugin = types.ModuleType(module_name)
            if package:
                plugin.__package__ = module_name
                plugin.__path__ = [self.path]
                sys.modules[module_name] = plugin
            else:
                plugin.__package__ = None
            sys.path.insert(0, self.path)
            with open(filepath) as f:
                code = compile(f.read(), filepath, 'exec')
                exec(code, plugin.__dict__)
            sys.path.remove(self.path)
            if package:
                del sys.modules[module_name]
        except Exception as err:
            raise RuntimeError(
                "Plugin '%s' at '%s' failed to load" % (self.name, self.path)
            ) from err

        return plugin

    def load(self):
        """loads the plugin file and returns the resulting module"""
        if self.mode == 'import':
            plugin = self._load_import()
        elif self.mode == 'exec':
            plugin = self._load_exec()
        else:
            raise RuntimeError(
                "Bad load mode '%s' for Plugin '%s' at '%s': "
                "'import' and 'exec' allowed"
                % (self.mode, self.name, self.path)
            )
        return plugin

    def get_version_string(self):
        """returns a version stirng"""
        return self.name + ":" + self.version[0]

    def run_on_enable(self):
        """runs the file in the 'on_enable' setting if set"""
        if self.on_enable:
            try:
                filepath = os.path.join(self.path, self.on_enable)
                sys.path.insert(0, self.path)
                with open(filepath) as f:
                    code = compile(f.read(), filepath, 'exec')
                    exec(code, {})
                sys.path.remove(self.path)
            except Exception as err:
                raise RuntimeError(
                    "Plugin '%s' at '%s' had an error during it's 'on_enable'"
                    % (self.name, self.path)
                ) from err

    def __str__(self):
        return "Plugin %s:%s" % (self.name, self.version[0], self.path)

    def __repr__(self):
        return "Plugin<%s:%s>@%s" % (self.name, self.version[0], self.path)


class System(object):

    """
    a plugin system
    It can scan dir trees to find plugins and their provided/needed components,
    and with a simple load call chain load all the plugins needed.

    the system includes a simple event system and fires some event,
    here are their signatures:

    'plugin_found' : (path, plugin)
        path : the full path to the folder containing the plugin
        plugin : plugin version string (ie 'plugin_name:version')

    'plugin_loaded' : (plugin, plugin_required, component_needed)
        plugin : plugin version string (ie 'plugin_name:version')
        plugin_required: version string of the plugin that required the
            loaded plugin (version string ie 'plugin_name:version')
        component_needed: the name of the component needed by the
            requesting plugin

    'component_loaded' : (component, plugin_required, plugin_loaded)
        component : the name of the component loaded
        plugin_required : version string of the plugin that required the
            loaded component (version string ie 'plugin_name:version')
            (might be None)
        plugin_loaded : version string of the plugin that the component was
            loaded from (version string ie 'plugin_name:version')

    Pyitect keeps track of all the instances of the System class in
    `System.systems` which is a map of object is's to instances of System.

    """
    systems = {}

    def __init__(self, config):
        """
        set up the system and load a configuration that may spesify plugins
        and versions to use for spesifc components
        plugins can define their own requerments but they are superceeded by
        the system configuration (carefull you can break it)
        """

        if not isinstance(config, collections.Mapping):
            raise RuntimeError(
                "System configurations must be mappings of component "
                "names to 'plugin:version' strings")

        self.config = config
        self.plugins = {}
        self.components = {}
        self.postfix_mappings = {}
        self.loaded_components = {}
        self.loaded_plugins = {}
        self.enabled_plugins = {}
        self.useing = {}
        self.events = {}
        System.systems[id(self)] = self

    def bind_event(self, event, function):
        """
        a simple event system bound to the plugin system,
        bind a function on an event and when the event is fired
        all bound functionsare called with args and kwargs
        passed to the fire call
        """
        if event not in self.events:
            self.events[event] = []
        self.events[event].append(function)

    def unbind_event(self, event, function):
        """
        remove a function from the event
        """
        if event in self.events:
            self.events[event].remove(function)

    def fire_event(self, event, *args, **kwargs):
        """
        fire all functions bound to the event name and pass all
        extra args and kwargs to the function
        """
        if event in self.events:
            for function in self.events[event]:
                function(*args, **kwargs)

    def _map_component(self, component, plugin, version):
        # either add the version or create a new array with the version and
        # save it
        if isinstance(version, str):
            version = (version, parse_version(version))
        if plugin in self.components[component]:
            self.components[component][plugin].append(version)
        else:
            self.components[component][plugin] = [version, ]
        self.fire_event('component_mapped', component, plugin, version)

    def _map_components(self, plugin_cfg):
        """
        takes a plugins metadata and remembers it's provided components so
        the system is awear of them
        """
        # loop through and map component names to a listing of plugin names and
        # versions
        if plugin_cfg.name not in self.enabled_plugins:
            self.enabled_plugins[plugin_cfg.name] = {}

        # store that the plugin is enabeled
        self.enabled_plugins[plugin_cfg.name][plugin_cfg.version] = plugin_cfg

        for component, mapping in plugin_cfg.provides.items():

            def map_postfix(mapping):
                arr = mapping.split("=")
                if len(arr) < 2:
                    raise RuntimeError(
                        "Plugin '%s' is trying to provide component '%s' with "
                        "an invalid mapping of '%s'"
                        % (plugin_cfg.name, component, mapping)
                    )
                postfix, mapped_name = arr
                postfix = postfix.strip()
                mapped_name = mapped_name.strip()
                version = plugin_cfg.version[0]
                if postfix:
                    version += '-' + postfix

                if plugin_cfg.name not in self.postfix_mappings:
                    self.postfix_mappings[plugin_cfg.name] = {}
                if component not in self.postfix_mappings[plugin_cfg.name]:
                    self.postfix_mappings[plugin_cfg.name][component] = {}
                self.postfix_mappings[plugin_cfg.name][
                    component][version] = mapped_name

                if plugin_cfg.name not in self.plugins:
                    self.plugins[plugin_cfg.name] = {}
                self.plugins[plugin_cfg.name][version] = plugin_cfg

                return version

            # ensure a place to list component providing plugin versions
            if component not in self.components:
                self.components[component] = {}
            if plugin_cfg.name not in self.components[component]:
                self.components[component][plugin_cfg.name] = []

            if mapping:
                mappings = mapping.split("|")
                if len(mappings) < 1:
                    self._map_component(
                        component, plugin_cfg.name, map_postfix(mappings))
                for pair in mappings:
                    self._map_component(
                        component, plugin_cfg.name, map_postfix(pair))
            else:
                self._map_component(
                    component, plugin_cfg.name, plugin_cfg.version)

        plugin_cfg.run_on_enable()

    def enable_plugins(self, plugins):
        """
        enables one or more plugins
        """
        if isinstance(plugins, collections.Mapping):
            # passed a dictionary
            for k in plugins:
                plugin = plugins[k]
                if not isinstance(plugin, Plugin):
                    raise RuntimeError(
                        "Object '%s' is not a plugin" % str(plugin))
                self._map_components(plugin)
        elif isinstance(plugins, collections.Iterable):
            # not a map but iterable
            for plugin in plugins:
                if not isinstance(plugin, Plugin):
                    raise RuntimeError(
                        "Object '%s' is not a plugin" % str(plugin))
                self._map_components(plugin)
        else:
            # single plugin
            plugin = plugins
            if not isinstance(plugin, Plugin):
                raise RuntimeError("Object '%s' is not a plugin" % str(plugin))
            self._map_components(plugin)

    def _add_plugin(self, path):
        """
        adds a plugin form the provided path
        """
        cfgpath = os.path.join(path, os.path.basename(path) + ".json")
        if os.path.exists(cfgpath):
            with open(cfgpath) as cfgfile:
                try:
                    cfg = json.load(cfgfile)
                except Exception as err:
                    raise RuntimeError(
                        "Could not parse plugin json file at '%s'" % path
                    ) from err

            if 'name' in cfg:
                # ensure we have a place to map the version to the config
                if not cfg['name'] in self.plugins:
                    self.plugins[cfg['name']] = {}
                # map the name and vserion to the config, use only the version
                # string not the full tuple
                plugin = Plugin(cfg, path)
                if (not self.plugins[cfg['name']] or
                        not self.plugins[cfg['name']][cfg['version']]):
                    self.plugins[cfg['name']][cfg['version']] = plugin
                    self.fire_event(
                        'plugin_found', path, plugin.get_version_string())
                else:
                    raise RuntimeError("Duplicate plugin name at '%s'" % path)
            else:
                raise RuntimeError("Plugin at %s has no name" % path)
        else:
            raise RuntimeError("No plugin exists at %s" % path)

    def _identify_plugin(self, path):
        """
        returns true if there is a plugin in the folder pointed to by path
        """
        # a plugin exists if a file with the same name as the folder + the
        # .json extention exists in the folder.
        names = os.listdir(path)
        name = os.path.basename(path) + ".json"
        if name in names:
            return True
        return False

    def _search_dir(self, folder):
        """
        recursivly searches a folder for plugins
        """
        # avoid recursion, could get nasty in a sificently big tree, also
        # faster.
        paths = [folder, ]
        while len(paths) > 0:
            # get the file names in the folder
            path = paths.pop(0)
            names = os.listdir(path)
            # loop through and identify plugins searching folders recursivly,
            # stops recursive if there is a plugin in the folder.
            for name in names:
                file = os.path.join(path, name)
                if os.path.isdir(file):
                    if self._identify_plugin(file):
                        self._add_plugin(file)
                    else:
                        paths.append(file)

    def search(self, path):
        """
        search a path (dir or file) for a plugin, in the case of a file it
        searches the containing dir.
        """
        # we either have a folder or a file,
        # if it's a file is there a plugin in the folder containing it?
        # if it's a folder are the plugins located somewhere within?
        if os.path.isdir(path):
            self._search_dir(path)
        else:
            self._add_plugin(os.path.dirname(path))

    @staticmethod
    def expand_version_requierment(version):
        """
        Takes a string of one of the following forms:

        "" -> no version requierment
        "*" -> no version requierment
        "plugin_name" -> spesfic plugin no version requierment
        "plugin_name:version_ranges" -> plugin version matches requirements

        and returns one of the following:

        ("", "") -> no version requierment
        ("plugin_name", "") -> plugin_name but no version requierment
        ("plugin_name", "verison_ranges")
        """
        if version == "*" or version == "":
            return ("", "")
        elif ":" in version:
            parts = version.split(":")
            if len(parts) != 2:
                raise RuntimeError(
                    "Version requirements can only contain at most 2 parts, "
                    "one plugin_name and one set of version requirements, "
                    "the parts seperated by a ':'")
            return (parts[0], parts[1])
        else:
            return (version,  "")

    def resolve_highest_match(self, component, plugin, version):
        """
        resolves the latest version of a component with requirements,
        passing empty strings means no requirements

        `version` Must match `version` exactly
        `>version` Must be greater than `version`
        `>=version` etc
        `<version`
        `<=version`
        `1.2` 1.2.0, 1.2.1, etc., but not 1.3.0
        `*` Matches any version
        "" (just an empty string) Same as *
        `version1 - version2` Same as `>=version1 <=version2`.
        `range1 || range2` Passes if either range1 or range2 are satisfied.
        """

        # we have no result yet
        result = None

        # if we've failed to give a requierment for somthing fill it ourselves
        if plugin == "":
            # we are gettign the first plugin name in a acending alpha-numeric
            # sort
            plugin = sorted(self.components[component])[0]

        if version == "":
            # sort the versions for the plugin and chouse the highest one, get
            # only the version string
            version = sorted(self.components[component][
                             plugin], key=operator.itemgetter(1), reverse=True
                             )[0][0]
            # if we've fallen back to the highest version we know of then there
            # is no point veryifying it's existance, we know of it after all
            result = (plugin, version)
            return result

        if plugin not in self.components[component]:
            raise RuntimeError(
                "Component '%s' is not provided by 'plugin' %s"
                % (component, plugin))

        # our requirements might pass if we satify one of a number of version
        # ranges
        version_ranges = []
        if " || " in version:
            # there are two or more version ranges, either could be satisfied
            version_ranges = version.split(" || ")
        else:
            version_ranges.append(version)

        # loop untill we run out of ranges to test or find a winner
        for version_range in version_ranges:

            # markers for the high and low version of the range
            # an empty string will mean infinite and the bool indicates if the
            # value is inclusive
            highv = ("", False)
            lowv = ("", False)

            # if the ends of the range are seperated with a dash
            if " - " in version_range:
                # if they've tried to mix syntaxes
                if (("=" in version_range) or
                        (">" in version_range) or
                        ("<" in version_range)):
                    raise RuntimeError(
                        "Versions ranges defined with a '-' can not include "
                        "additional spesifers like '=<>' ")
                high_low = version_range.split(" - ")
                # be sure we onyl have two versions
                if len(high_low) != 2:
                    raise RuntimeError(
                        "Version ranges defined with a '-' must included "
                        "exactly 2 versions, a high and a low")
                highv = (high_low[0], True)
                lowv = (high_low[1], True)
            elif " " in version_range:
                parts = version_range.split(" ")

                if len(parts) != 2:
                    raise RuntimeError(
                        "In versions useing the implicit `and` of a space "
                        "(" ") between version statements, there may only "
                        "be 2 version statments")

                # they are useing implicit and, all parts must either include a
                # > or a < +/- an =, both must be present
                wakagreaterflag = False
                wakaleserflag = False

                # we also need to establish which is the high and which is the
                # low
                for part in parts:
                    equalto = (part[1] == "=")
                    if part[0] == ">":
                        wakagreaterflag = True
                        lowv = (part[1:].lstrip("="), equalto)
                    elif part[0] == "<":
                        wakaleserflag = True
                        highv = (part[1:].lstrip("="), equalto)

                if not (wakagreaterflag and wakaleserflag):
                    raise RuntimeError(
                        "In versions useing the implicit and of a space (" ") "
                        "between version statements, all parts must include "
                        "either a greater or lesser-than symbol at their "
                        "begining, both must be in use")

            else:
                # we only have one version statment
                statment = version_range.strip().lstrip("=")

                equalto = False
                if ">=" in statment or "<=" in statment:
                    equalto = (statment[1] == "=")
                if statment[0] == ">":
                    wakagreaterflag = True
                    lowv = (statment[1:], equalto)
                elif statment[0] == "<":
                    wakaleserflag = True
                    highv = (statment[1:], equalto)
                elif statment != "*" and statment != "":
                    highv = lowv = (statment, True)

            # now we parse the high and low versions to make them compairable
            # and find a suitable version
            highv = (highv[0], parse_version(highv[0]), highv[1])
            lowv = (lowv[0], parse_version(lowv[0]), lowv[1])

            # sorted from highest to lowest
            sorted_versions = sorted(
                self.components[component][plugin],
                key=operator.itemgetter(1),
                reverse=True
            )

            # loop striping off verisons that are too high or too low
            while True:
                stripdone = False
                # if there is even a limit
                if highv[0] != "":
                    # if the high value is inclusive
                    if highv[2]:
                        if sorted_versions[0][1] > highv[1]:
                            sorted_versions = sorted_versions[1:]
                            stripdone = True
                    else:
                        if sorted_versions[0][1] >= highv[1]:
                            sorted_versions = sorted_versions[1:]
                            stripdone = True

                # if there is even a limit
                if lowv[0] != "":
                    # if the low value is inclusive
                    if lowv[2]:
                        if (sorted_versions[len(sorted_versions) - 1][1] <
                                lowv[1]):
                            sorted_versions = sorted_versions[
                                :len(sorted_versions) - 1]
                            stripdone = True
                    else:
                        if (sorted_versions[len(sorted_versions) - 1][1] <=
                                lowv[1]):
                            sorted_versions = sorted_versions[
                                :len(sorted_versions) - 1]
                            stripdone = True

                if not stripdone or len(sorted_versions) < 1:
                    break

            if len(sorted_versions) < 1:
                raise RuntimeError(
                    "Component '%s' does not have any providers that meet "
                    "requirements" % component)

            result = (plugin, sorted_versions[0][0])
            return result

    def ittrPluginsByComponent(self, compon, requirements=None):
        """
        iterates over the all possible providers of a component
        returning the plugin name and the highest version possible.
        if there are postfix version mappings for a component in a plugin
        iterates over them too.
        """
        for plugin_name, versions in self.components[compon].items():
            version_req = ""
            if (requirements is not None and plugin_name in requirements):
                version_req = requirements[plugin_name]
            plug, version = self.resolve_highest_match(
                compon, plugin_name, version_req)
            if plug in self.postfix_mappings:
                if compon in self.postfix_mappings[plug]:
                    # we dont want to double list versions
                    if version not in self.postfix_mappings[plug][compon]:
                        yield (plug, version)
                    for postfix_ver in self.postfix_mappings[plug][compon]:
                        yield (plug, postfix_ver)
                else:
                    yield (plug, version)
            else:
                yield (plug, version)

    def _load_component(self, component, plugin, version, requesting=None):

        # be sure not to load things twice, but besure the components is loaded
        # and saved
        if component not in self.loaded_components:
            self.loaded_components[component] = {}
        if plugin not in self.loaded_components[component]:
            self.loaded_components[component][plugin] = {}
        if version not in self.loaded_components[component][plugin]:

            plugin_obj = self.load_plugin(
                plugin, version, requesting=requesting, component=component)

            access_name = component
            if (plugin in self.postfix_mappings and
                    component in self.postfix_mappings[plugin] and
                    version in self.postfix_mappings[plugin][component]):
                access_name = self.postfix_mappings[plugin][component][version]
            if not hasattr(plugin_obj, access_name):
                raise RuntimeError(
                    "Plugin '%s:%s' does not have name '%s'"
                    % (plugin, version, access_name))

            self.loaded_components[component][plugin][
                version] = getattr(plugin_obj, access_name)

            # record the use of this component, perhaps so the users can save
            # the configuration
            if component not in self.useing:
                self.useing[component] = {}
            if plugin not in self.useing[component]:
                self.useing[component][plugin] = []
            if version not in self.useing[component][plugin]:
                self.useing[component][plugin].append(version)

            self.fire_event(
                'component_loaded',
                component,
                requesting,
                plugin + ":" + version
            )

        component_obj = self.loaded_components[component][plugin][version]
        return component_obj

    def load_plugin(self, plugin, version, requesting=None, component=None):
        # we dont want to load a plugin twice just becasue it provides more
        # than one component, save previouly loaded plugins
        if plugin not in self.loaded_plugins:
            self.loaded_plugins[plugin] = {}
        if version not in self.loaded_plugins[plugin]:
            # create a blank module namespace to attach our equired components
            consumes = types.ModuleType("PyitectConsumes")

            plugin_cfg = self.plugins[plugin][version]

            for component_req in plugin_cfg.consumes.keys():
                try:
                    setattr(
                        consumes,
                        component_req,
                        self.load(
                            component_req,
                            plugin_cfg.consumes,
                            requesting=plugin_cfg.get_version_string()
                        )
                    )
                except Exception as err:
                    raise RuntimeError(
                        "Could not load required component "
                        "'%s' for plugin '%s@%s'"
                        % (component_req, plugin, version)
                    ) from err

            sys.modules["PyitectConsumes"] = consumes
            self.loaded_plugins[plugin][version] = plugin_cfg.load()
            del sys.modules["PyitectConsumes"]
            self.fire_event(
                'plugin_loded',
                plugin_cfg.get_version_string(),
                requesting,
                component
            )

        plugin_obj = self.loaded_plugins[plugin][version]
        return plugin_obj

    def load(self, component, requires=None, requesting=None, bypass=False):
        """
        processes loading and returns the component by name,
        chain loading any required plugins to obtain dependencies.
        Uses the config that was provided on system creation
        to load correct versions, if there is a conflist throws
        a run time error.
        bypass lets the call bypass the system configuration
        """
        # set default requirements
        plugin = version = plugin_req = version_req = ""
        if component not in self.components:
            raise RuntimeError(
                "Component '%s' not provided by any enabled plugins"
                % component)

        # merge the systems config and the passed plugin requirements (if they
        # were passed) to get the most relavent requirements
        reqs = {}

        if not bypass:
            reqs.update(self.config)
        if requires is not None:
            reqs.update(requires)

        # update the plugin and version requirements if they exist
        if component in reqs:
            plugin_req, version_req = System.expand_version_requierment(
                reqs[component])
        else:
            warnings.warn(RuntimeWarning(
                "Component '%s' has no default provided, defaulting to "
                "alphabetical order"
                % component))

        # get the plugin and version to load
        plugin, version = self.resolve_highest_match(
            component, plugin_req, version_req)

        component = self._load_component(component, plugin, version)

        return component

    def get_plugin_module(self, plugin, version=None):
        if plugin in self.loaded_plugins:
            if not version:
                version = sorted(
                    self.loaded_plugins[plugin].keys(), reverse=True)[0]
            if version in self.loaded_plugins[plugin]:
                return self.loaded_plugins[plugin][version]
            else:
                raise RuntimeError(
                    "Version '%s' of plugin '%s' not yet loaded"
                    % (version, plugin))
        else:
            raise RuntimeError("Plugin '%s' not yet loaded" % plugin)


def parse_version(version_str):
    component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)
    components = [
        x
        for x in component_re.split(version_str)
        if x and x != '.'
    ]
    for i, obj in enumerate(components):
        try:
            components[i] = int(obj)
        except ValueError:
            pass
    return tuple(components)
