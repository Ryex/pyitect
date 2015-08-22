import sys
import re
import hashlib
import warnings
from semantic_version import Version, Spec

PY_VER = sys.version_info[:2]
PY2 = PY_VER[0] == 2

# fix types for Python2+ supprot
try:
    basestring
except NameError:
    basestring = str


def _str_encode(obj):
    # ensure bytes is there in Python2
    if PY2:
        return str(obj)
    else:
        return str(obj).encode()


def get_unique_name(*parts):
    name_hash = hashlib.sha1()
    for part in parts:
        name_hash.update(_str_encode(part))
    return str(name_hash.hexdigest())


def walk_qual_name(name):
    """Attempts to walk fully qualified name to obtain the object

    Args:
        name (str): a dot '.' seperated string of names
        walkable form sys.modules

    Raises:
        KeyError: when module does not exist
        AttributeError: when part of the names can not be found
    """
    parts = name.split(".")
    obj = sys.modules[parts[0]]
    for part in parts[1:]
        obj = getattr(obj, part)
    return obj


def gen_version(version_str):
    """
    generates an internally used version tuple
    generates a 2 tuple
    preserving the original version string in the first position
    a parsed version in the second
    """
    try:
        ver = Version(version_str)
    except ValueError:
        ver = Version.coerce(version_str)
