import importlib
import json
import sys
import os
import collections
import warnings

class Plugin(object):
    
    def __init__(self, config, path):
        if hasattr(config, 'name'):
            self.name = config.name
        else:
            raise RuntimeError("Plugin as %s does not have a name" % path)
        if hasattr(config, 'author'):
            self.author = config.author
        else:
            raise RuntimeError("Plugin as %s does not have an author" % path)
        if hasattr(config, 'version'):
            self.version = config.version
        else:
            raise RuntimeError("Plugin as %s does not have a version" % path)
        if hasattr(config, 'file'):
            self.file = config.file
        else:
            raise RuntimeError("Plugin as %s does not have a plugin file spesified" % path)
        if hasattr(config, 'consumes') and isinstance(config.consumes, collections.Mapping):
            self.consumes = config.consumes
        else:
            raise RuntimeError("Plugin as %s does not have a maping of consumed components to versions" % path)
        if hasattr(config, 'provides') and isinstance(config.provides, collections.Mapping):
            self.provides = config.provides
        else:
            raise RuntimeError("Plugin as %s does not have a maping of provided components to versions" % path)
        self.path = path
        
    def load(self):
        filepath = importlib.find_loader(os.path.join(self.path, self.name))
        spec = importlib.util.spec_from_file_location(self.name, filepath)
        plugin = spec.loader.load_module()
        return plugin
        
class System(object):
    
    def __init__(self, config):
        self.config = config
        self.plugins = {}
        self.components = {}
        self.loaded = {}
        self.useing = {}
        
    def load_plugin(self, plugin_cfg):
        
        # loop through and add the plugin's provided components, only done at plugin load
        for key, value in plugin_cfg.provides:
            pass
        
    def map_components(self, plugin_cfg):
        #loop through and map component names to a listing of plugin names and versions
        for name, version in plugin_cfg.provides:
            # ensure a place to list component providing plugin versions
            if not name in self.components:
                self.components[name] = {}
            
            # either add the version or create a new array with the version and save it
            if plugin_cfg.name in self.components[name]:
                self.components[name][plugin_cfg.name].append(version)
            else:
                self.components[name][plugin_cfg.name] = [version, ]
                
                    
    def add_plugin(self, path):
        cfgpath = os.path.join(path, os.path.basename(path) + ".json")
        if os.path.exists(cfgpath):
            cfgfile = open(cfgpath)
            cfg = json.load(cfgfile)
            
            if hasattr(cfg, 'name'):

                # ensure we have a place to map the version to the config 
                if not cfg.name in self.plugins:
                    self.plugins[cfg.name] = {}
                
                # map the name and vserion to the config
                self.plugins[cfg.name][cfg.version] = Plugin(cfg, path)
                
            else:
                raise RuntimeError("Plugin at %s has no name" % path)
        else:
            raise RuntimeError("No plugin exists at %s" % path)
            
    def identify_plugin(self, path):
        # a plugin exists if a file with the same name as the folder + the .json extention exists in the folder.
        names = os.listdir(path)
        name = os.path.basename(path) + ".json"
        if name in names:
            return true
        return false
        
    def search_dir(self, path)
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
        # we either have a folder or a file, 
        # if it's a file is there a plugin in the folder containing it? 
        # if it's a folder are the plugins located somewhere within?
        if os.path.isdir(path):
            self.search_dir(path)
        else:
            self.add_plugin(os.path.dirname(path))
            
    def load(self, component):
        """ 
        processes loading and returns the component by name, 
        chain loading any required plugins to obtain dependencies. 
        Uses the config that was provided on system creation to load correct versions, 
        if there is aconflist throws a run time error.
        """
        if not component in self.components:
            raise RuntimeError("Component %s not provided by any loaded plugins" % component)
        if not component in self.config:
            warnings.warn(RuntimeWarning("Component %s has no default provided, defaulting to"))