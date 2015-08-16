import sys
import re
import hashlib

PY_VER = sys.version_info[:2]
PY2 = PY_VER[0] == 2

# ensure bytes is there in Python2

def _str_encode(obj):
    if PY2:
        return str(obj)
    else:
        return str(obj).encode()

def get_unique_name(name, author, version, extra=None):
    name_hash = hashlib.sha1()
    name_hash.update( _str_encode(name))
    name_hash.update( _str_encode(author))
    name_hash.update( _str_encode(version))
    if extra:
        name_hash.update( _str_encode(extra))
    return str(name_hash.hexdigest())

def gen_version(version_str):
    """
    generates an internally used version tuple
    generates a 2 tuple
    preserving the original version string in the first position
    a parsed version in the second
    """
    return (version_str, parse_version(version_str))


def parse_version(version_str):
    """
    dumbly parses a version string into it's parts
    attempts to covert from string to integers where possible
    """
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
