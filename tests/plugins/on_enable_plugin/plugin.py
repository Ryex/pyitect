from __future__ import (print_function)

import sys


def foofoofoo():
    return "foofoofoo"


def on_enable_foo_func(plugin):
    print(plugin)
    sys.PYTITECT_TEST = True
