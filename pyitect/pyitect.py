from __future__ import (print_function)

import sys

import os

from .utils import PY_VER
from .utils import gen_version
from .utils import get_unique_name
from .utils import cmp_version_spec
from .utils import parse_version_spec
from .utils import expand_version_req

have_importlib = PY_VER >= (3, 4)

if have_importlib:
    import importlib.util
else:
    import imp

import json

import collections
import warnings
import operator
from semantic_version import Version, Spec

# fix types for Python2+ supprot
try:
    basestring
except NameError:
    basestring = str

_have_yaml = False
try:
    import yaml
    _have_yaml = True
except ImportError:
    pass


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
            raise ValueError(
                "Plugin as '%s' does not have a name string" % path)
        if 'author' in config and isinstance(config['author'], basestring):
            self.author = config['author'].strip()
        else:
            raise ValueError(
                "Plugin as '%s' does not have a author string" % path)
        if 'version' in config:
            # store both the original version string and a parsed version that
            # can be compaired accurately
            self.version = gen_version(config['version'].strip())
        else:
            raise ValueError("Plugin at '%s' does not have a version" % path)
        if 'file' in config:
            self.file = config['file'].strip()
        else:
            raise ValueError(
                "Plugin as '%s' does not have a plugin file spesified" % path)
        if (('consumes' in config) and
                isinstance(config['consumes'], collections.Mapping)):
            self.consumes = config['consumes']
        else:
            raise ValueError(
                "Plugin at '%s' has no map of consumed "
                "components to plugin versions" % path)
        if (('provides' in config) and
                isinstance(config['provides'], collections.Mapping)):
            self.provides = config['provides']
        else:
            raise ValueError(
                "Plugin at '%s' hs no map of provided components"
                " to version postfixes" % path)
        if 'on_enable' in config:
            if isinstance(config['on_enable'], basestring):
                self.on_enable = config['on_enable']
            else:
                raise ValueError(
                    "Plugin at '%s' has a 'on_enable' that is not a string"
                    % path)
        else:
            self.on_enable = None
        self.path = path
        self.module = None

    def _load(self):
        global PY2
        # import can handle cases where the file isn't a python source file,
        # for example a compiled pyhton module in the form of a .pyd or .so
        # only works with pyhton 3.4+
        filepath = os.path.join(self.path, self.file)
        module_name = get_unique_name(self.author, self.get_version_string())
        if have_importlib:
            try:
                sys.path.insert(0, self.path)
                spec = importlib.util.spec_from_file_location(
                    module_name, filepath)
                plugin = spec.loader.load_module()
                sys.path.remove(self.path)
            except Exception as err:
                message = (
                    str(err) + "\nPlugin '%s' at '%s' failed to load"
                    % (self.name, self.path))
                err.strerror = message
                raise err
        else:
            name = os.path.splitext(os.path.basename(self.file))[0]
            search_path = self.path
            if name == "__init__":
                name = os.path.basename(self.path)
                search_path = os.path.dirname(self.path)
            try:
                sys.path.insert(0, search_path)
                f, pathn, desc = imp.find_module(name, [search_path])
                try:
                    plugin = imp.load_module(module_name, f, pathn, desc)
                except Exception as err:
                    message = (
                        str(err) + "\nPlugin '%s' at '%s' failed to load"
                        % (self.name, self.path))
                    err.strerror = message
                    raise err
                finally:
                    if f:
                        f.close()
                sys.path.remove(search_path)
            except Exception as err:
                message = (
                    str(err) + "\nPlugin '%s' at '%s' failed to load"
                    % (self.name, self.path))
                err.strerror = message
                raise err

        return plugin

    def load(self):
        """loads the plugin file and returns the resulting module"""
        if self.module is None:
            plugin = self._load()
            self.module = plugin
        return self.module

    def get_version_string(self):
        """returns a version stirng"""
        return self.name + ":" + str(self.version)

    def run_on_enable(self):
        """runs the file in the 'on_enable' setting if set"""
        if self.on_enable:
            parts = self.on_enable.split(".")
            if len(parts) < 1:
                raise RuntimeError(
                    "Plugin '%s' at '%s' has an invalid object path "
                    "in its on_enable"
                    % (self.name, self.path)
                    )
            if self.module is None:
                raise RuntimeError(
                    "Plugin '%s' at '%s' has no module object and is not "
                    "loaded yet. can not attempt to find on_enable function"
                    % (self.name, self.path)
                    )
            obj = self.module
            try:
                for part in parts:
                    obj = getattr(obj, part)
            except Exception as err:
                message = (
                    str(err) + "\nPlugin '%s' at '%s' "
                    "can not access 'on_enable' path '%s'"
                    % (self.name, self.path, self.on_enable))
                err.strerror = message
                raise err

            if not callable(obj):
                message = (
                    str(err) + "\nPlugin '%s' at '%s' "
                    "can not call 'on_enable' path '%s', not callable"
                    % (self.name, self.path, self.on_enable))
                err.strerror = message
                raise err

            obj()

    def has_on_enable(self):
        return (self.on_enable is not None) and (not self.on_enable == "")

    def __str__(self):
        return "Plugin %s:%s" % (self.name, self.version)

    def __repr__(self):
        return "Plugin<%s:%s>@%s" % (self.name, self.version, self.path)


class Component(object):

    def __init__(self, name, path, plugin, version, obj):
        if not isinstance(name, basestring):
            raise TypeError("name must be a string component name")
        if not isinstance(path, basestring):
            raise TypeError("path must be a str fully qualified name of obj")
        if not isinstance(plugin, basestring):
            raise TypeError("plugin must be a string plugin name")
        if not isinstance(version, tuple):
            raise TypeError("must be a tuple representing a version")
        self.name = name
        self.path = path
        self.plugin = plugin
        self.version = version
        self.obj = obj

    def __call__(self):
        return self.obj

    def __eq__(self, other):
        if not isinstance(other, Component):
            return False
        if not self.name == other.name:
            return False
        if not self.path == other.path:
            return False
        if not self.plugin == other.plugin:
            return False
        if not self.version == other.version:
            return False
        return True

    def __hash__(self):
        return hash((self.name, self.path, self.plugin, self.version))


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
    `System.systems` which is a map of object id's to instances of System.

    """
    systems = {}

    def __init__(self, config, enable_yaml=False):
        """
        set up the system and load a configuration that may spesify plugins
        and versions to use for spesifc components
        plugins can define their own requerments but they are superceeded by
        the system configuration (carefull you can break it)
        """
        global _have_yaml

        if not isinstance(config, collections.Mapping):
            raise RuntimeError(
                "System configurations must be mappings of component "
                "names to 'plugin:version' strings")

        if _have_yaml and enable_yaml:
            self._yaml = True
        else:
            self._yaml = False

        self.config = config
        self.plugins = {}
        self.components = {}
        self.postfix_mappings = {}
        self.loaded_components = {}
        self.loaded_plugins = {}
        self.enabled_plugins = {}
        self.using = {}
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
        if isinstance(version, basestring):
            version = gen_version(version)
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
                version = plugin_cfg.version
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

    def _enable_plugins_map(self, plugins):
        on_enables = []
        for k in plugins:
            plugin = plugins[k]
            if not isinstance(plugin, Plugin):
                raise RuntimeError(
                    "'%r' is not a plugin" % str(plugin))
            if plugin.has_on_enable():
                on_enables.append(plugin)
            self._map_components(plugin)
        return on_enables

    def _enable_plugins_iter(self, plugins):
        on_enables = []
        for plugin in plugins:
            if not isinstance(plugin, Plugin):
                raise RuntimeError(
                    "'%r' is not a plugin" % str(plugin))
            if plugin.has_on_enable():
                on_enables.append(plugin)
            self._map_components(plugin)
        return on_enables

    def enable_plugins(self, *plugins):
        """
        enables one or more plugins
        """
        if len(plugins) == 1:
            plugins = plugins[0]

        if isinstance(plugins, collections.Mapping):
            # passed a dictionary
            on_enables = self._enable_plugins_map(plugins)
        elif isinstance(plugins, collections.Iterable):
            # not a map but iterable
            on_enables = self._enable_plugins_iter(plugins)
        else:
            # single plugin
            plugin = plugins
            if not isinstance(plugin, Plugin):
                raise RuntimeError("'%r' is not a plugin" % str(plugin))
            if plugin.has_on_enable():
                    on_enables.append(plugin)
            self._map_components(plugin)
        self._run_on_enables(on_enables)

    def _run_on_enables(self, *plugins):
        if len(plugins) == 1:
            plugins = plugins[0]
        if isinstance(plugins, Plugin):
            self.load_plugin(
                plugins.name,
                plugins.version,
                plugins.get_version_string() + ":on_enable")
            plugins.run_on_enable()
        elif isinstance(plugins, collections.Iterable):
            for plugin in plugins:
                self.load_plugin(
                    plugin.name,
                    plugin.version,
                    plugin.get_version_string() + ":on_enable")
                plugin.run_on_enable()

    def _read_plugin_cfg(self, path, is_yaml=False):
        with open(path) as cfgfile:
            if (is_yaml and self._yaml):
                try:
                    cfg = yaml.load(cfgfile)
                except Exception as err:
                    message = (
                        str(err) +
                        "\nCould not parse plugin yaml file at %s"
                        % (path,))
                    err.strerror = message
                    raise err
            else:
                try:
                    cfg = json.load(cfgfile)
                except Exception as err:
                    message = (
                        str(err) +
                        "\nCould not parse plugin json file at %s"
                        % (path,))
                    err.strerror = message
                    raise err
        return cfg

    def _add_plugin(self, path):
        """
        adds a plugin form the provided path
        """
        exts = (".yml", ".yaml", ".json")
        yamls = (".yml", ".yaml")
        cfgpath = None
        is_yaml = False

        for ext in exts:
            cfgpath = os.path.join(path, os.path.basename(path) + ext)
            if os.path.exists(cfgpath):
                if ext in yamls:
                    is_yaml = True
                break

        if cfgpath is not None:

            cfg = self._read_plugin_cfg(cfgpath, is_yaml)

            if 'name' in cfg:
                # ensure we have a place to map the version to the config
                if cfg['name'] not in self.plugins:
                    self.plugins[cfg['name']] = {}
                if cfg['version'] not in self.plugins[cfg['name']]:
                    # map the name and vserion to the config
                    # use only the version string not the full tuple
                    plugin = Plugin(cfg, path)
                    self.plugins[cfg['name']][cfg['version']] = plugin
                    self.fire_event(
                        'plugin_found', path, plugin.get_version_string())
                else:
                    raise RuntimeError(
                        "Duplicate plugin %s@%s at '%s'"
                        % (cfg['name'], cfg['version'], path))
            else:
                raise RuntimeError("Plugin at %s has no name" % (path,))
        else:
            raise RuntimeError("No plugin exists at %s" % (path,))

    def _identify_plugin(self, path):
        """
        returns true if there is a plugin in the folder pointed to by path
        """
        # a plugin exists if a file with the same name as the folder + the
        # .json (or .yml/.yaml if yaml is enabled)
        # extention exists in the folder.
        names = os.listdir(path)
        exts = [".json"]
        if self._yaml:
            exts.extend([".yml", ".yaml"])
        for ext in exts:
            name = os.path.basename(path) + ext
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

    def _find_matching_versions(self, component, plugin, spec):
        # sorted from highest to lowest
        sorted_versions = sorted(
            self.components[component][plugin],
            key=operator.itemgetter(1),
            reverse=True
            )

        valid_versions = []

        while sorted_versions:
            version = sorted_versions.pop(0)
            if cmp_version_spec(version[1], spec):
                valid_versions.append(version)

        return valid_versions

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

        specs = parse_version_spec(version)

        valid_versions = self._find_matching_versions(component, plugin, specs)

        if len(valid_versions) < 1:
            raise RuntimeError(
                "Component '%s' does not have any providers that meet "
                "requirements" % component)

        sorted_versions = sorted(
            valid_versions,
            key=operator.itemgetter(1),
            reverse=True
            )

        return plugin, sorted_versions[0][0]

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
            if component not in self.using:
                self.using[component] = {}
            if plugin not in self.using[component]:
                self.using[component][plugin] = []
            if version not in self.using[component][plugin]:
                self.using[component][plugin].append(version)

            self.fire_event(
                'component_loaded',
                component,
                requesting,
                plugin + ":" + version
                )

        component_obj = self.loaded_components[component][plugin][version]
        return component_obj

    def load_plugin(self, plugin, version, requesting=None, component=None):
        """
        takes a plugin name and version and finds the stored Plugin object
        takes a Plugin object and loads the module
        recursively loading declared dependencies
        """
        # we dont want to load a plugin twice just becasue it provides more
        # than one component, save previouly loaded plugins
        if plugin not in self.loaded_plugins:
            self.loaded_plugins[plugin] = {}
        if version not in self.loaded_plugins[plugin]:
            if ((plugin not in self.plugins) or
                    (version not in self.plugins[plugin])):
                raise RuntimeError(
                    "Plugin system has no pluign '%s' at version '%s'"
                    % (plugin, version)
                    )
            plugin_cfg = self.plugins[plugin][version]
            # collect the imports namespace object
            imports = sys.modules[__name__.split('.')[0]].imports
            # loop through the consumed component names
            # load them and add them to the imports namespace
            for req_name in plugin_cfg.consumes.keys():
                obj = None
                try:
                    obj = self.load(
                        req_name,
                        plugin_cfg.consumes,
                        requesting=plugin_cfg.get_version_string()
                        )
                except Exception as err:
                    message = (
                        str(err) + "\nCould not load required component "
                        "'%s' for plugin '%s@%s'"
                        % (req_name, plugin, version))
                    err.strerror = message
                    raise err
                setattr(imports, req_name, obj)

            # load the plugin
            self.loaded_plugins[plugin][version] = plugin_cfg.load()

            # cleanup the imports namespace
            for req_name in plugin_cfg.consumes.keys():
                delattr(imports, req_name)
            self.fire_event(
                'plugin_loaded',
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
        to load correct versions, if there is a conflict throws
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
            plugin_req, version_req = expand_version_req(reqs[component])
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
        """
        searches for the highest version number plugin with it's module loaded
        if it can't find  it it raises a runtime error
        """
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


def issubcomponent(comp1, comp2):
    """Check if comp1 is a subtype of comp2

    Returns whether the Component passed as comp1 validates
    as a subtype of the Component passed as comp2.

    if strings are passed as either peramater they are treated as Component
    names. if a Component instance is passed it's `name` property is pulled.

    Args:
        comp1 (str, Component): The Component or component name to check
        comp2 (str, Component): The Component or component name to compair to
    """
    if isinstance(comp1, Component):
        comp1 = comp1.name
    if isinstance(comp2, Component):
        comp2 = comp2.name
    if not isinstance(comp1, basestring):
        raise TypeError("comp1 must either be a string name or Component")
    if not isinstance(comp2, basestring):
        raise TypeError("comp2 must either be a string name or Component")

    comp1_parts = comp1.split(".")
    comp2_parts = comp2.split(".")

    if len(comp2_parts) < len(comp1_parts):
        return False

    if not tuple(comp1_parts) == tuple(comp2_parts[:len(comp1_parts)]):
        return False

    return True
