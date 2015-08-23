from __future__ import (print_function)

import sys

import os

PY_VER = sys.version_info[:2]
PY2 = PY_VER[0] == 2
have_importlib = PY_VER >= (3, 4)

if have_importlib:
    import importlib.util
else:
    import imp

import json

import collections
import hashlib

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

    """An object that can hold the metadata for a plugin

    like its name, author, verison, and the file to be loaded ect.
    also stores the path to the plugin folder and provideds functionality
    to load the plugin module and run its `on_enable` function


    Attributes:
        name (str): plugin name
        author (str): plugin author
        version (Version): plugin vesion
        file (str): relative path to the file to import to load the plugin
        consumes (dict): a listing of the components consumed
        provides (dict): a listing of the components provided
        on_enable (None, str): either `None` or a str doted name of a function
            in the module
        path (str): an absolute path to the plugin folder
        module (None, object): either `None` or the modlue object if the plugin
            has been loaded already

    """

    def __init__(self, config, path):
        """Init the plugin container object

        and pull information from it's passed config,
        storing the path where it can be found

        Args:
            config (dict): a mapping object that holds data from a config file
            path (str): the absolute path to the plugin's folder

        Raises:
            ValueError: when any of the config keys are wrong
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

    def key(self):
        """return a key that can be used to identify the plugin

        Returns:
            tuple: (name, author, version, path)
        """
        return (self.name, self.author, self.version, self.path)

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
        """returns a version string"""
        return self.name + ":" + str(self.version)

    def run_on_enable(self):
        """runs the function in the 'on_enable' if set"""
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

            obj(self)

    def has_on_enable(self):
        """returns `True` if it has an `on_enable` attribute that's not None"""
        return (self.on_enable is not None) and (not self.on_enable == "")

    def __str__(self):
        return self.get_version_string()

    def __repr__(self):
        return "Plugin(%s:%s@%s)" % (self.name, self.version, self.path)

    def __eq__(self, other):
        if not isinstance(other, Plugin):
            return False
        if not self.key() == other.key():
            return False
        return True

    def __hash__(self):
        return hash(self.key())


class Component(object):
    """An object to hold metadata for a spesfic instance of a component

    Holds the metadata needed to identify a instance of a component
    provided by a plugin

    Attributes:
        name (str): the component name provided
        plugin (str): the name of the providing plugin
        author (str): the author of the providing plugin
        version (Version): the verison of the providing plugin
        path (str): a doted name path to the component object from the top
            of the plugin module
    """

    def __init__(self, name, plugin, author, version, path):
        """Init the component object

        Args:
            name (str): the component name provided
            plugin (str): the name of the providing plugin
            author (str): the author of the providing plugin
            version (Version, str): the verison of the providing plugin
            path (str): a doted name path to the component object from the top
                of the plugin module
        """
        if not isinstance(name, basestring):
            raise TypeError("name must be a string component name")
        if not isinstance(plugin, basestring):
            raise TypeError("plugin must be a string plugin name")
        if not isinstance(author, basestring):
            raise TypeError("author must be a string author name")
        if isinstance(version, basestring):
            version = gen_version(version)
        if not isinstance(version, Version):
            raise TypeError("must be a SemVer Version")
        if not isinstance(path, basestring):
            raise TypeError("path must be a string path to object")
        self.name = name
        self.author = author
        self.plugin = plugin
        self.version = version
        self.path = path

    def key(self):
        """returns a key to identify this component

        Returns:
            tuple: (name, plugin, author, version, path)
        """
        return (self.name, self.plugin, self.author, self.version, self.path)

    def __eq__(self, other):
        if not isinstance(other, Component):
            return False
        if not self.key() == other.key():
            return False
        return True

    def __hash__(self):
        return hash(self.key())


class System(object):
    """A plugin system

    It can scan dir trees to find plugins and their provided/needed components,
    and with a simple load call chain load all the plugins needed.

    The system includes a simple event system and fires some events internal,
    here are their signatures:

    'plugin_found': (path, plugin)
        path (str): the full path to the folder containing the plugin

        plugin (str): plugin version string (ie 'plugin_name:version')

    'plugin_loaded': (plugin, plugin_required, component_needed)
        plugin (str): plugin version string (ie 'plugin_name:version')

        plugin_required (str): version string of the plugin that required the
        loaded plugin (version string ie 'plugin_name:version')

        component_needed (str): the name of the component needed by the
        requesting plugin

    'component_loaded': (component, plugin_required, plugin_loaded)
        component (str): the name of the component loaded

        plugin_required (str, None): version string of the plugin that
        required the loaded component
        (version string ie 'plugin_name:version')
        (might be None)

        plugin_loaded (str): version string of the plugin that the component
        was loaded from (version string ie 'plugin_name:version')

    Pyitect keeps track of all the instances of the System class in
    `System.systems` which is a map of object id's to instances of System.

    Attributes:

        config (dict): A mapping of component names to version requirements
        plugins (dict): A mapping of the plugins the system knows about.
            Maps names to `dicts` of :class:`Version` s mapped to
            :class:`Plugin` config objects

        components (dict): A mapping of :func:`Component.key` s to
            loaded component objects

        component_map (dict): A mapping of components the system knows about.
            Maps names to `dicts` of :class:`Version` s mapped to
            :class:`Component` config objects

        loaded_plugins (dict): A mapping of :func:`Plugin.key` s to
            loaded plugin module objects

        enabled_plugins (list): A list of :func:`Plugin.key` s of
            enabled plugins

        using (list): A List of :func:`Component.key` s loaded by the system

        events (dict): A mapping of event names to lists of callable objects

    """

    systems = []
    """A list of all :class:`System` instances"""

    def __init__(self, config, enable_yaml=False):
        """Setup the system and load a configuration

        that may spesify plugins and versions to use for spesifc components
        plugins can define their own requerments the system configuration
        acts as a default (carefull you can break it)

        Args:
            config (dict): A mapping of component names to version requirements
            enable_yaml (bool): Should the system support yaml config files?
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
        self.component_map = {}
        self.loaded_plugins = {}
        self.enabled_plugins = []
        self.using = []
        self.events = {}
        System.systems.append(self)

    def bind_event(self, event, function):
        """Bind a callable object to the event name

        a simple event system bound to the plugin system,
        bind a function on an event and when the event is fired
        all bound functions are called with the `*args` and `**kwargs`
        passed to the fire call

        Args:
            event (str): name of event to bind to
            function (callable): Boject to be called when event fires
        """
        if event not in self.events:
            self.events[event] = []
        self.events[event].append(function)

    def unbind_event(self, event, function):
        """Remove a function from an event

        removes the function object from the list of callables
        to call when event fires. does nothing if function is not bound

        Args:
            event (str): name of event bound to
            function (callable): object to unbind
        """
        if event in self.events:
            self.events[event].remove(function)

    def fire_event(self, event, *args, **kwargs):
        """Call all functions bound to the event name

        and pass all extra `*args` and `**kwargs` to the bound functions

        Args:
            event (str): name of event to fire
        """
        if event in self.events:
            for function in self.events[event]:
                function(*args, **kwargs)

    def iter_component_subtypes(self, component):
        """An iterater function to interate all known subtypes of a component

        Takes a conponent name and yeilds all known conponent names that
        are subtypes not including the conponent name

        Args:
            conponent (str): the conponent name to act as a base
        """
        if isinstance(component, Component):
            component = component.name
        if not isinstance(component, basestring):
            raise ValueError(
                "%r  object is niether a Component instance nor a string"
                % (component,))

        for key in self.component_map:
            if issubcomponent(key, component) and component != key:
                yield key

    def iter_component_providers(self, comp, subs=False, vers=False, reqs="*"):
        """An iterater function to interate providers of a component

        Takes a conponent name and yeilds providers of the conponent

        if `subs` is `True` yeilds providers of subtypes too

        if `vers` is `True` yeilds all version of the provider
        not just the highest

        `reqs` is a version requirement for the providers to meet.
        Defaults to any version

        Args:
            comp (str): component name to use as a base
            subs (bool): should subtypes be yeilded too?
            vers (bool): should all version be yeilded not just the highest?
            reqs (str, list, tuple): version spec string or list there of
            all items are passed to a :class:`Spec`
        """
        if isinstance(reqs, basestring):
            reqs = (reqs,)
        if not isinstance(reqs, (list, tuple)):
            raise ValueError(
                "Invalid requierment type, must be string, list, or tuple: %r"
                % (reqs,))
        if not isinstance(comp, basestring):
            raise ValueError(
                "comp is niether a Component instance nor a string: %r"
                % (comp,))

        spec = Spec(*reqs)

        if subs:
            comps = self.component_map.keys()
        else:
            comps = (comp,)

        for com in comps:
            if com in self.component_map and issubcomponent(com, comp):
                providers = self.component_map[com]
                for prov in providers:
                    versions = providers[prov]
                    if vers:
                        for ver in sorted(versions):
                            yield (com, prov, ver)
                    else:
                        yield (com, prov, spec.select(versions))

    def _enable_plugin(self, plugin):
        # loop through and map component names to a listing of plugin names and
        # versions

        # save the plugin as enabled
        plugin_key = (plugin.name, plugin.version)
        if plugin_key not in self.enabled_plugins:
            self.enabled_plugins.append(plugin_key)

        for name, path in plugin.provides.items():

            # ensure a place to list component providing plugin versions
            if name not in self.component_map:
                self.component_map[name] = {}
            if plugin.name not in self.component_map[name]:
                self.component_map[name][plugin.name] = {}
            if plugin.version in self.component_map[name][plugin.name]:
                raise RuntimeError(
                    "Duplicate component %s provided by plugin %s@%s"
                    % (name, plugin.name, plugin.version))

            if not path:
                path = name

            component = Component(
                name,
                plugin.name,
                plugin.author,
                plugin.version,
                path)

            self.component_map[name][plugin.name][plugin.version] = component

    def _enable_plugins_map(self, plugins):
        on_enables = []
        for k in plugins:
            plugin = plugins[k]
            if not isinstance(plugin, Plugin):
                raise RuntimeError(
                    "'%r' is not a plugin" % str(plugin))
            if plugin.has_on_enable():
                on_enables.append(plugin)
            self._enable_plugin(plugin)
        return on_enables

    def _enable_plugins_iter(self, plugins):
        on_enables = []
        for plugin in plugins:
            if not isinstance(plugin, Plugin):
                raise RuntimeError(
                    "'%r' is not a plugin" % str(plugin))
            if plugin.has_on_enable():
                on_enables.append(plugin)
            self._enable_plugin(plugin)
        return on_enables

    def enable_plugins(self, *plugins):
        """Take one or more `Plugin` s and map it's components

        Takes a plugins metadata and remembers it's provided components so
        the system is awear of them

        Args:
            plugins (plugins): One or more plugins to enable.
            Each argument can it self be a list or map of :class:`Plugin`
            objects or a plain :class:`Plugin` object
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
            self._enable_plugin(plugin)
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
                    cfg = yaml.safe_load(cfgfile)
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

    def add_plugin(self, path):
        """Adds a plugin form the provided path

        Args:
            path (str): path to a plugin folder
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

        if cfgpath is not None and os.path.exists(cfgpath):

            cfg = self._read_plugin_cfg(cfgpath, is_yaml)

            plugin = Plugin(cfg, path)
            name = plugin.name
            version = plugin.version
            if name not in self.plugins:
                self.plugins[name] = {}

            if version in self.plugins[name]:
                raise RuntimeError(
                    "Duplicate plugin %s@%s at '%s'"
                    % (name, version, path))

            self.plugins[name][version] = plugin
            self.fire_event('plugin_found', path, plugin.get_version_string())

        else:
            raise RuntimeError("No plugin exists at %s" % (path,))

    def is_plugin(self, path):
        """Test a path to see if it is a `Plugin`

        Args:
            path (str): path to test

        Returns: true if there is a plugin in the folder pointed to by path
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
                    if self.is_plugin(file):
                        self.add_plugin(file)
                    else:
                        paths.append(file)

    def search(self, path):
        """Search a path (dir or file) for a plugin
        in the case of a file it searches the containing dir.

        Args:
            path (str): the path to search
        """
        # we either have a folder or a file,
        # if it's a file is there a plugin in the folder containing it?
        # if it's a folder are the plugins located somewhere within?
        if os.path.isdir(path):
            self._search_dir(path)
        else:
            self.add_plugin(os.path.dirname(path))

    def resolve_highest_match(self, component, plugin, spec):
        """resolves the latest version of a component with requirements,

        takes in a component name and some requierments and gets a valid plugin
        name and its highest version

        Args:
            component (str): a component name
            plugin (str): a plugin name
                if it's empty we default to alphabetical order
            spec (Spec): a SemVer version spec

        Raises:
            TypeError: if somthing isn't the right type

        """
        if not isinstance(component, basestring):
            raise TypeError(
                "component must be a component name string, "
                "got: %r" % (component,))
        if not isinstance(plugin, basestring):
            raise TypeError(
                "plugin must be a plugin name string, "
                "got: %r" % (plugin,))
        if not isinstance(spec, Spec):
            raise TypeError(
                "Version spec must be a SemVer version spec, "
                "got: %r" % (spec,))

        if component not in self.component_map:
            raise RuntimeError(
                "Component '%s' is not provided by any plugin"
                % (component,))

        # if we've failed to give a requierment for somthing fill it ourselves
        if plugin == "":
            # we are gettign the first plugin name in a acending alpha-numeric
            # sort
            plugin = sorted(list(self.component_map[component].keys()))[0]

        if plugin not in self.component_map[component]:
            raise RuntimeError(
                "Component '%s' is not provided by plugin '%s'"
                % (component, plugin))

        versions = self.component_map[component][plugin].keys()
        highest_valid = spec.select(versions)

        if not highest_valid:
            raise RuntimeError(
                "Component '%s' does not have any providers that meet "
                "requirements" % component)

        return plugin, highest_valid

    def _load_component(self, component, plugin,
                        version, requires=None, request=None):

        # be sure not to load things twice, but besure the components is loaded
        # and saved
        if not isinstance(component, basestring):
            raise TypeError(
                "component must be a component name string, "
                "got: %r" % (component,))
        if not isinstance(plugin, basestring):
            raise TypeError(
                "plugin must be a plugin name string, "
                "got: %r" % (plugin,))
        if isinstance(version, basestring):
            version = gen_version(version)
        if not isinstance(version, Version):
            raise TypeError(
                "Version must be a SemVer Version, "
                "got: %r" % (version,))
        if component not in self.component_map:
            raise RuntimeError(
                "Component '%s' is not provided by any plugin"
                % (component,))
        if (plugin not in self.component_map[component]
                or version not in self.component_map[component][plugin]):
            raise RuntimeError(
                "Component '%s' is not provided by plugin '%s@%s'"
                % (component, plugin, version))

        comp = self.component_map[component][plugin][version]

        key = comp.key()
        if key not in self.components:

            plugin_obj = self.load_plugin(
                plugin, version,
                requires=requires, request=request, comp=component)

            obj = plugin_obj
            parts = comp.path.split(".")
            for part in parts:
                if not hasattr(obj, part):
                    raise RuntimeError(
                        "Plugin '%s:%s' does not have name '%s'"
                        % (plugin, version, comp.path))
                obj = getattr(obj, part)

            self.components[key] = obj

            # record the use of this component, perhaps so the users can save
            # the configuration
            self.using.append(key)

            self.fire_event(
                'component_loaded',
                component,
                request,
                plugin + ":" + str(version)
                )

        return self.components[key]

    def load_plugin(self, plugin, version,
                    requires=None, request=None, comp=None):
        """Takes a plugin name and version and loads it's module

        finds the stored Plugin object
        takes a Plugin object and loads the module
        recursively loading declared dependencies

        Args:
            plugin (str): plugin name

            version (str, Version): version to load

            requires (dict, None): a mapping of component names
            to version requierments to use during the load

            request (str, None): name of the version string of the plugin
            that requested a component from this plugin.
            `None` if not requested.

            comp (str): name of the component needed by teh requesting plugin.
            `None` if not requested.

        Returns:
            the loaded module object
        """
        # we dont want to load a plugin twice just becasue it provides more
        # than one component, save previouly loaded plugins
        if isinstance(version, basestring):
            version = gen_version(version)
        if not isinstance(plugin, basestring):
            raise TypeError(
                "plugin must be a plugin name string, "
                "got: %r" % (plugin,))
        if not isinstance(version, Version):
            raise TypeError(
                "Version must be a SemVer Version, "
                "got: %r" % (version,))
        plugin_key = (plugin, version)
        if plugin_key not in self.loaded_plugins:
            if (plugin not in self.plugins
                    or version not in self.plugins[plugin]):
                raise RuntimeError(
                    "System has no plugin '%s' at version '%s'"
                    % (plugin, version))
            cfg = self.plugins[plugin][version]
            # collect the imports namespace object
            imports = sys.modules[__name__.split('.')[0]].imports
            # loop through the consumed component names
            # load them and add them to the imports namespace
            for req_name in cfg.consumes.keys():
                obj = None
                try:
                    obj = self.load(
                        req_name,
                        cfg.consumes,
                        requires=requires,
                        request=cfg.get_version_string()
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
            self.loaded_plugins[plugin_key] = cfg.load()

            # cleanup the imports namespace
            for req_name in cfg.consumes.keys():
                delattr(imports, req_name)
            self.fire_event(
                'plugin_loaded',
                cfg.get_version_string(),
                request,
                comp
                )
        plugin_obj = self.loaded_plugins[plugin_key]
        return plugin_obj

    def load(self, component, requires=None, request=None, bypass=False):
        """Load and return a component object

        processes loading and returns the component by name,
        chain loading any required plugins to obtain dependencies.
        Uses the config that was provided on system creation
        to load correct versions, if there is a conflict throws
        a run time error.
        bypass lets the call bypass the system configuration

        Args:
            component (str): name of component to load

            requires (dict, None): a mapping of component names
            to version requierments to use during the load

            request (str, None): the name of the requesting plugin.
            `None` if not requested

            bypass (bool): ignore the system configured version requierments

        Returns:
            the loaded component object

        """
        # set default requirements
        plugin = version = plugin_req = ""
        version_spec = Spec("*")
        if component not in self.component_map:
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
            plugin_req, version_spec = expand_version_req(reqs[component])

        # get the plugin and version to load
        plugin, version = self.resolve_highest_match(
            component, plugin_req, version_spec)

        comp_obj = self._load_component(
            component, plugin, version, requires=reqs)

        return comp_obj

    def get_plugin_module(self, plugin, version=None):
        """Fetch the loaded plugin module

        if `version` is None
        searches for the highest version number plugin with it's module loaded
        if it can't find anything it raises a runtime error

        Args:
            plugin (str): name of plugin to find
            version (None, str, Version): if provided load a spesfic version

        Returns:
            loaded module object

        Raises:
            TypeError: if provideing a version that is not either a `str` or
            a :class:`Version`
            RuntimeError: if the Plugin can't be found or is not loaded yet
        """
        if version:
            if isinstance(version, basestring):
                version = gen_version(version)
            if not isinstance(version, Version):
                raise TypeError(
                    "Version must be a SemVer Version, "
                    "got: %r" % (version,))
        if plugin in self.plugins:
            if not version:
                version = sorted(
                    self.plugins[plugin].keys(), reverse=True)[0]
            plugin_key = (plugin, version)
            if plugin_key in self.loaded_plugins:
                return self.loaded_plugins[plugin_key]
            else:
                raise RuntimeError(
                    "Version '%s' of plugin '%s' not yet loaded"
                    % (version, plugin))
        else:
            raise RuntimeError("Plugin '%s' not found" % plugin)


def expand_version_req(requires):
    """Take a requierment and return the Spec and the plugin name

    takes a requierment and pumps out a plugin name and a SemVer Spec
    requires is either a string of the form
    `("", "*", "plugin_name", plugin_name:version_spec)`

    or a mapping with `plugin` and `spec` keys like so
    `{"plugin": "plugin_name", "spec": ">=1.0.0"}`
    the spec key's value can be a string of comma seperated version
    requierments or a list of strings of the same

    Args:
        requires (str, mapping):
            string or mapping object with `plugin` and `spec` keys

    Examples:

        >>> expand_version_req("")
        ('', <Spec: (<SpecItem: * ''>,)>)
        >>> expand_version_req("*")
        ('', <Spec: (<SpecItem: * ''>,)>)
        >>> expand_version_req("plugin_name")
        ('plugin_name', <Spec: (<SpecItem: * ''>,)>)
        >>> expand_version_req("plugin_name:>=1.0.0")
        ('plugin_name', <Spec: (<SpecItem: >= Version('1.0.0')>,)>)
        >>> expand_version_req("plugin_name:>=1.0.0,<2.0.0")
        ('plugin_name', <Spec: (SpecItems... >= 1.0.0, < 2.0.0 )>)
        >>> expand_version_req({"plugin": "plugin_name", "spec": ">=1.0.0"})
        ('plugin_name', <Spec: (<SpecItem: >= Version('1.0.0')>,)>)

    Raises:
        ValueError: when the requierment is of a bad form
        TypeError: when the requiers objt is not a string or mapping

    """
    if isinstance(requires, basestring):
        if requires == "*" or requires == "":
            return ("", Spec("*"))
        elif ":" in requires:
            parts = requires.split(":")
            if len(parts) != 2:
                raise ValueError(
                    "Version requirements strings can only contain "
                    "at most 2 parts, "
                    "one plugin_name and one set of version requirements, "
                    "the parts seperated by a ':'")
            return (parts[0], Spec(parts[1]))
        else:
            return (requires,  Spec("*"))
    elif isinstance(requires, collections.Mapping):
        if "plugin" not in requires:
            raise ValueError(
                "Version requirements mappings must contain a 'plugin' key")
        if "spec" not in requires:
            raise ValueError(
                "Version requirements mappings must contain a 'spec' key")
        return (requires["plugin"], Spec(requires["spec"]))
    else:
        raise TypeError(
            "Invalid type of requires object, "
            "must be a string or mapping object: %r"
            % (requires,))


def gen_version(version_str):
    """Generates an :class:`Version` object

    takes a SemVer string and returns a :class:`Version`
    if not a proper SemVer string it coerces it

    Args:
        version_str (str): version string to use
    """
    try:
        ver = Version(version_str)
    except ValueError:
        ver = Version.coerce(version_str)
    return ver


def get_unique_name(*parts):
    """Generate a fixed lenght unique name from parts

    takes the parts turns them into strings and uses them in a sha1 hash

    used internaly to ensure module object for plugins have unique names
    like so

    `get_unique_name(plugin.author, plugin.get_version_string())`

    Returns:
        str: name hash
    """
    def _str_encode(obj):
        # ensure bytes is there in Python2
        if PY2:
            return str(obj)
        else:
            return str(obj).encode()
    name_hash = hashlib.sha1()
    for part in parts:
        name_hash.update(_str_encode(part))
    return str(name_hash.hexdigest())


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
