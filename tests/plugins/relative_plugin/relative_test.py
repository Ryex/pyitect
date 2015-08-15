from __future__ import (print_function)

print("relative_test.py", __name__, __package__)


class TestClass(object):

    def __init__(self, message):
        self.message = message

    def hello(self):
        print(self.message)
