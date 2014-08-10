import importlib
import json
import sys
import os
import collections
import warnings
from pkg_resources import parse_version
import operator
import itertools

class Namespace(object):
    """
    dummy class to hold namespaces during plugin loading
    """
    pass

def expand_version_requierment(version):
        """
        Takes a string of one of the following forms:
        
        "" -> no version requierment
        "*" -> no version requierment
        "plugin_name" -> spesfic plugin no version requierment
        "plugin_name:version_ranges" -> spesfic plugin version matches requierments
        
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
                raise RuntimeError("Version requierments can only contain at most 2 parts, one plugin_name and one set of version requierments, the parts seperated by a ':'")
            return (parts[0], parts[1] )
        else:
            return (version,  "")

         

class Plugin(object):
    """
    an object that can hold the metadata for a plugin, like its name, author, verison, and the file to be loaded ect.
    """
    
    def __init__(self, config, path):
        if 'name' in config:
            self.name = config['name']
        else:
            raise RuntimeError("Plugin as %s does not have a name" % path)
        if 'author' in config:
            self.author = config['author']
        else:
            raise RuntimeError("Plugin as %s does not have an author" % path)
        if 'version' in config:
            #store both the original version string and a parsed version that can be compaired accurately
            self.version = (config['version'], parse_version(config['version']))
        else:
            raise RuntimeError("Plugin as %s does not have a version" % path)
        if 'file' in config:
            self.file = config['file']
        else:
            raise RuntimeError("Plugin as %s does not have a plugin file spesified" % path)
        if 'consumes' in config and isinstance(config['consumes'], collections.Mapping):
            self.consumes = config['consumes']
        else:
            raise RuntimeError("Plugin as %s does not have a maping of consumed components to plugin versions" % path)
        if 'provides' in config and isinstance(config['provides'], collections.Iterable):
            self.provides = config['provides']
        else:
            raise RuntimeError("Plugin as %s does not have a list provided components" % path)
        self.path = path
        
    def load(self):
        filepath = os.path.join(self.path, self.file)
        spec = importlib.util.spec_from_file_location(self.name, filepath)
        plugin = spec.loader.load_module()
        return plugin
        
class System(object):
    """
    a plugin system
    It can scan folder trees to find plugins and their provided/needed components, 
    and with a simple load call chain load all the plugins needed.
    """
    
    def __init__(self, config):
        """
        set up the system and load a configuration that may spesify plugins and versions to use for spesifc components
        plugins can define their own requerments but they are superceeded by the system configuration (carefull you can break it)
        """
        
        if not isinstance(config, collections.Mapping):
            raise RuntimeError("System configurations must be mapings of component names to 'plugin:version' strings")
        
        self.config = config
        self.plugins = {}
        self.components = {}
        self.loaded_components = {}
        self.loaded_plugins = {}
        self.useing = {}
        
    def map_components(self, plugin_cfg):
        """
        takes a plugins meta data and remembers it's provided components so they system is awear of them
        """
        #loop through and map component names to a listing of plugin names and versions
    
        for name in plugin_cfg.provides:
            # ensure a place to list component providing plugin versions
            if not name in self.components:
                self.components[name] = {}
            
            # either add the version or create a new array with the version and save it
            if plugin_cfg.name in self.components[name]:
                self.components[name][plugin_cfg.name].append(plugin_cfg.version)
            else:
                self.components[name][plugin_cfg.name] = [plugin_cfg.version, ]
                
                    
    def add_plugin(self, path):
        """
        adds a plugin form the provided path
        """
        cfgpath = os.path.join(path, os.path.basename(path) + ".json")
        if os.path.exists(cfgpath):
            cfgfile = open(cfgpath)
            cfg = json.load(cfgfile)
            
            if 'name' in cfg:
                # ensure we have a place to map the version to the config 
                if not cfg['name'] in self.plugins:
                    self.plugins[cfg['name']] = {}
                # map the name and vserion to the config, use only the version string not the full tuple
                plugin = Plugin(cfg, path)
                self.plugins[cfg['name']][cfg['version']] = plugin
                self.map_components(plugin)
            else:
                raise RuntimeError("Plugin at %s has no name" % path)
        else:
            raise RuntimeError("No plugin exists at %s" % path)
            
    def identify_plugin(self, path):
        """
        returns true if there is a plugin in the folder pointed to by path
        """
        # a plugin exists if a file with the same name as the folder + the .json extention exists in the folder.
        names = os.listdir(path)
        name = os.path.basename(path) + ".json"
        if name in names:
            return True
        return False
        
    def search_dir(self, path):
        """
        recursivly searches a folder for plugins
        """
        # get the file names in the folder
        names = os.listdir(path)
        # loop through and identify plugins searching folders recursivly, stops recursive if there is a plugin in the folder.
        for name in names:
            file = os.path.join(path, name)
            if os.path.isdir(file):
                if self.identify_plugin(file):
                    self.add_plugin(file)
                else:
                    self.search_dir(path)
                
    def search(self, path):
        """
        search a path (folder or file) for a plugin, in the case of a file it searches the containing folder.
        """
        # we either have a folder or a file, 
        # if it's a file is there a plugin in the folder containing it? 
        # if it's a folder are the plugins located somewhere within?
        if os.path.isdir(path):
            self.search_dir(path)
        else:
            self.add_plugin(os.path.dirname(path))
            
    def resolve_highest_match(self, component, plugin, version):
        """
        resolves the latest version of a compoent with requierments, passing empty strings means no requierments

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
            # we are gettign the first plugin name in a acending alpha-numeric sort
            plugin = sorted(self.components[component])[0]
            
        if version == "":
            # sort the versions for the plugin and chouse the highest one, get only the version string
            version = sorted(self.components[component][plugin], key=operator.itemgetter(1), reverse=True)[0][0]
            # if we've fallen back to the highest version we know of then there is no point veryifying it's existance, we know of it after all
            result = (plugin, version)
            return result
            
        if not plugin in self.components[component]:
            raise RuntimeError("Component '%s' is not provided by 'plugin' %s" % (component, plugin))
        
        # our requerments might pass if we satify one of a number of version ranges
        version_ranges = []
        if " || " in version:
            # there are two or more version ranges, either could be satisfied
            version_ranges = version.split(" || ")
        else:
            version_ranges.append(version)
            
        # loop untill we run out of ranges to test or find a winner
        for version_range in version_ranges:
            
            #markers for the high and low version of the range
            #an empty string will mean infinite and the bool indicates if the value is inclusive
            highv =  ("", False) 
            lowv = ("", False)
            
            #if the ends of the range are seperated with a dash
            if " - " in version_range:
                # if they've tried to mix syntaxes
                if ("=" in version_range) or (">" in version_range) or ("<" in version_range):
                    raise RuntimeError("Versions ranges defined with a '-' can not include additional spesifers like '=<>' ")
                high_low = version_range.split(" - ")
                #be sure we onyl have two versions
                if len(high_low) != 2:
                    raise RuntimeError("Version ranges defined with a '-' can must included exactly 2 versions, a high and a low")
                highv = (high_low[0], True)
                lowv = (high_low[1], True)
            elif " " in version_range:
                parts = version_range.split(" ")
                
                if len(parts) != 2:
                   raise RuntimeError("In versions useing the implicit and of a space (" ") between verison statements, there may only be 2 version statments") 
                
                #they are useing implicit and, all parts must either include a > or a < +/- an =, both must be present
                wakagreaterflag = False
                wakaleserflag = False
                
                #we also need to establish which is the high and which is the low
                for part in parts:
                    equalto = (part[1] == "=")
                    if part[0] == ">":
                        wakagreaterflag = True
                        lowv = (part[1:].lstrip("="), equalto)
                    elif part[0] == "<":
                        wakaleserflag = True
                        highv = (part[1:].lstrip("="), equalto)
                        
                if not (wakagreaterflag and wakaleserflag):
                    raise RuntimeError("In versions useing the implicit and of a space (" ") between verison statements, all parts must include  either a greater or lesser-than symbolat their begining, both must be in use")
                
            else:
                # we only have one version statment
                statment = version_range.strip().lstrip("=")
                equalto = (statment[1] == "=")
                if statment[0] == ">":
                    wakagreaterflag = True
                    lowv = (statment[1:], equalto)
                elif statment[0] == "<":
                    wakaleserflag = True
                    highv = (statment[1:], equalto)
                elif statment != "*" and statment != "":
                    highv = lowv = (statment, True)
            
            # now we parse the high and low versions to make them compairable and find a suitable version
            highv = (highv[0], parse_version(highv[0]), highv[1])
            lowv = (lowv[0], parse_version(lowv[0]), lowv[1])
            
            # sorted from highest to lowest
            sorted_versions = sorted(self.components[component][plugin], key=operator.itemgetter(1), reverse=True)
            
            #loop striping off verisons that are too high or too low
            while True:
                stripdone = False
                #if there is even a limit
                if highv[0] != "":
                    #if the high value is inclusive
                    if highv[2]:
                        if sorted_versions[0][1] > highv[1]:
                            sorted_versions = sorted_versions[1:]
                            stripdone = True
                    else:
                        if sorted_versions[0][1] >= highv[1]:
                            sorted_versions = sorted_versions[1:]
                            stripdone = True
                            
                #if there is even a limit
                if lowv[0] != "":
                    # if the low value is inclusive
                    if lowv[2]:
                        if sorted_versions[len(sorted_versions) - 1][1] < lowv[1]:
                            sorted_versions = sorted_versions[:len(sorted_versions) - 1]
                            stripdone = True
                    else:
                        if sorted_versions[len(sorted_versions) - 1][1] <= lowv[1]:
                            sorted_versions = sorted_versions[:len(sorted_versions) - 1]
                            stripdone = True
                        
                if not stripdone:
                    break
                
            if len(sorted_versions) < 1:
                raise RuntimeError("Component '%s' does not have any providers that meet requierments" % component)
                
            result = (plugin, sorted_versions[0][0])
            return result
                
            
    def load(self, component, requierments=None):
        """ 
        processes loading and returns the component by name, 
        chain loading any required plugins to obtain dependencies. 
        Uses the config that was provided on system creation to load correct versions, 
        if there is a conflist throws a run time error.
        """
        #set default requierments
        plugin = version = plugin_req = version_req = ""
        if not component in self.components:
            raise RuntimeError("Component '%s' not provided by any loaded plugins" % component)
        if not component in self.config:
            warnings.warn(RuntimeWarning("Component '%s' has no default provided, defaulting to alphabetical order" % component))
        
        # merge the systems config and the passed plugin requierments (if they were passed) to get the most relavent requierments
        reqs = {}
        
        if not requierments is None:
            reqs.update(requierments)
        reqs.update(self.config)
        
        # update the plugin and version requierments if they exist
        if component in reqs:
            plugin_req, version_req = expand_version_requierment(reqs[component])
            
        # get the plugin and version to load
        plugin, version = self.resolve_highest_match(component, plugin_req, version_req)
        
        # be sure not to load things twice, but besure the compoents is loaded and saved
        if not component in self.loaded_components:
            self.loaded_components[component] = {}
        if not plugin in self.loaded_components[component]:
            self.loaded_components[component][plugin] = {}
        if not version in self.loaded_components[component][plugin]:
            
            #we dont want to load a plugin twice just becasue it provides more than one component, save previouly loaded plugins
            if not plugin in self.loaded_plugins:
                self.loaded_plugins[plugin] = {}
            if not version in self.loaded_plugins[plugin]:
                #we'll use this to store the needed components for the plugin we'll be loading
                consumes = Namespace.__new__(Namespace)
                
                plugin_cfg = self.plugins[plugin][version]
                
                for component_req in plugin_cfg.consumes.keys():
                    setattr(consumes, component_req, self.load(component_req, plugin_cfg.consumes))
                    
                sys.modules["PyitectConsumes"] = consumes
                self.loaded_plugins[plugin][version] = plugin_cfg.load()
                del sys.modules["PyitectConsumes"]
            
            plugin_obj = self.loaded_plugins[plugin][version]
            if not hasattr(plugin_obj, component):
                raise RuntimeError("Plugin '%s:%s' dose not have component '%s'" % (plugin, version, component) )
                
            self.loaded_components[component][plugin][version] = getattr(plugin_obj, component)
            
        #record the use of this component, perhaps so the users can save the configuration
        if not component in self.useing:
            self.useing[component] = {}
        if not plugin in self.useing[component]:
            self.useing[component][plugin] = []
        if not version in self.useing[component][plugin]:
            self.useing[component][plugin].append(version)
            
        return self.loaded_components[component][plugin][version]
