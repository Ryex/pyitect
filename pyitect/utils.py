import sys
import re
import hashlib
import warnings

PY_VER = sys.version_info[:2]
PY2 = PY_VER[0] == 2


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


def gen_version(version_str):
    """
    generates an internally used version tuple
    generates a 2 tuple
    preserving the original version string in the first position
    a parsed version in the second
    """
    return (version_str, parse_version(version_str))


def parse_version_spec(version):

    if '(' in version or ')' in version:
        raise RuntimeError("Perns can not be used in version strings")

    if '||' in version:
        specs = tuple([parse_version_spec(s) for s in version.split('||')])
        return (specs, '||')

    if ' ' in version:
        specs = tuple([parse_version_spec(s) for s in version.split(' ')])
        return (specs, '&&')

    if '&&' in version:
        specs = tuple([parse_version_spec(s) for s in version.split('&&')])
        return (specs, '&&')

    if ' - ' in version:
        return parse_version_spec_range(version)

    return parse_version_spec_oper(version)


def parse_version_spec_range(version):
    # if they've tried to mix syntaxes
    if (("=" in version) or
            (">" in version) or
            ("<" in version)):
        raise RuntimeError(
            "Versions ranges defined with a '-' can not include "
            "additional spesifers like '=<>' ")
    high_low = version.split(" - ")
    # be sure we only have two versions
    if len(high_low) != 2:
        raise RuntimeError(
            "Version ranges defined with a '-' must included "
            "exactly 2 versions, a high and a low")

    versions = [parse_version(v) for v in high_low]
    sorted_versions = sorted(versions)
    highv = ((sorted_versions[0],), '<=')
    lowv = ((sorted_versions[1],), '>=')
    return ((highv, lowv), '&&')


def parse_version_spec_oper(version):
    if version[:2] == "==":
        return ((parse_version_spec_dot_x(version[2:]),), '==')
    if version[:2] == ">=" or version[:2] == "=>":
        return ((parse_version_spec_dot_x(version[2:]),), '>=')
    if version[:2] == "<=" or version[:2] == "=<":
        return ((parse_version_spec_dot_x(version[2:]),), '<=')
    if version[:2] == "!=" or version[:2] == "=!":
        return ((parse_version_spec_dot_x(version[2:]),), '!=')
    if version[:1] == "<":
        return ((parse_version_spec_dot_x(version[1:]),), '<')
    if version[:1] == ">":
        return ((parse_version_spec_dot_x(version[1:]),), '>')
    if version[:1] == "=":
        return ((parse_version_spec_dot_x(version[1:]),), '==')
    if version[:1] == "!":
        return ((parse_version_spec_dot_x(version[1:]),), '!')
    return ((parse_version_spec_dot_x(version),), '==')


def parse_version_spec_dot_x(version):
    """
    dumbly parses a version string into it's parts
    attempts to covert from string to integers where possible
    """
    clear_str = version.strip()
    if clear_str[-2:] == ".x":
        base_ver = parse_version(clear_str[:-2])
        to_big_ver = [x for x in base_ver]
        if not isinstance(to_big_ver[-1], int):
            warnings.warn(RuntimeWarning(
                "Series notation *.x for z.y.x for version "
                "requierments only works if y is an integer"))
            return parse_version(clear_str)
        to_big_ver[-1] = int(to_big_ver[-1]) + 1
        return (
            ((base_ver,), '>='),
            ((tuple(to_big_ver),), '<'),
            '&&')
    return parse_version(clear_str)


def cmp_version_spec(version, spec):

    if len(spec[0]) > 1:
        # this is an and/or/not spec
        return cmp_verison_spec_and_or_not(version, spec)
    else:
        return cmp_version_oper(version, spec)


def cmp_verison_spec_and_or_not(version, spec):
    if spec[1] not in ('&&', '||', '!'):
        raise RuntimeError("Bad spec oper %s" % spec[1])
    if spec[1] == "&&":
        return cmp_version_spec_and(version, spec)
    elif spec[1] == '||':
        return cmp_version_spec_or(version, spec)
    elif spec[1] == '!':
        return cmp_version_spec_not(version, spec)


def cmp_version_spec_and(version, spec):
    for sub in spec[0]:
        if not cmp_version_spec(version, sub):
            return False
    return True


def cmp_version_spec_or(version, spec):
    for sub in spec[0]:
        if cmp_version_spec(version, sub):
            return True
    return False


def cmp_version_spec_not(version, spec):
    for sub in spec[0]:
        if cmp_version_spec(version, sub):
            return False
    return True


def cmp_version_oper(version, spec):
    if spec[1] not in ('>', '<', "<=", '>=', "==", "!="):
        raise RuntimeError("Bad spec oper %s" % spec[1])
    if spec[1] == '==':
        return cmp_version_eq(version, spec[0][0])
    if spec[1] == '!=':
        return cmp_version_ne(version, spec[0][0])
    elif spec[1] == '<':
        return cmp_version_lt(version, spec[0][0])
    elif spec[1] == '>':
        return cmp_version_gt(version, spec[0][0])
    elif spec[1] == '<=':
        return (cmp_version_lt(version, spec[0][0])
                or cmp_version_eq(version, spec[0][0]))
    elif spec[1] == '>=':
        return (cmp_version_gt(version, spec[0][0])
                or cmp_version_eq(version, spec[0][0]))


def cmp_version_eq(version, version_spec):
    return version == version_spec


def cmp_version_ne(version, version_spec):
    return version != version_spec


def cmp_version_lt(version, version_spec):
    return version < version_spec


def cmp_version_gt(version, version_spec):
    return version > version_spec


def parse_version(version_str):
    """
    dumbly parses a version string into it's parts
    attempts to covert from string to integers where possible
    """
    component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)
    components = [
        x
        for x in component_re.split(version_str.strip())
        if x and x != '.'
        ]
    for i, obj in enumerate(components):
        try:
            components[i] = int(obj)
        except ValueError:
            pass
    return tuple(components)


def expand_version_req(version):
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
