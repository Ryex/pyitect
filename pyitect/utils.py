"""
This file containes code for raise_from under pyhton 2 and python 3
This code was copyied from the python-future package

Copyright (c) 2013-2015 Python Charmers Pty Ltd, Australia

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

PY2 = False
if sys.version_info[0] == 2:
    PY2 = True

if PY2:
    def raise_from(exc, cause):
        """
        Equivalent to:
            raise EXCEPTION from CAUSE
        on Python 3. (See PEP 3134).
        """
        # Is either arg an exception class (e.g. IndexError) rather than
        # instance (e.g. IndexError('my message here')? If so, pass the
        # name of the class undisturbed through to "raise ... from ...".
        if isinstance(exc, type) and issubclass(exc, Exception):
            e = exc()
            # exc = exc.__name__
            # execstr = "e = " + _repr_strip(exc) + "()"
            # myglobals, mylocals = _get_caller_globals_and_locals()
            # exec(execstr, myglobals, mylocals)
        else:
            e = exc
        e.__suppress_context__ = False
        if isinstance(cause, type) and issubclass(cause, Exception):
            e.__cause__ = cause()
            e.__suppress_context__ = True
        elif cause is None:
            e.__cause__ = None
            e.__suppress_context__ = True
        elif isinstance(cause, BaseException):
            e.__cause__ = cause
            e.__suppress_context__ = True
        else:
            raise TypeError("exception causes must derive from BaseException")
        e.__context__ = sys.exc_info()[1]
        raise e

else:
    def raise_from(exc, cause):
        """
        Equivalent to:
            raise EXCEPTION from CAUSE
        on Python 3. (See PEP 3134).
        """
        # Is either arg an exception class (e.g. IndexError) rather than
        # instance (e.g. IndexError('my message here')? If so, pass the
        # name of the class undisturbed through to "raise ... from ...".
        if isinstance(exc, type) and issubclass(exc, Exception):
            exc = exc.__name__
        if isinstance(cause, type) and issubclass(cause, Exception):
            cause = cause.__name__
        execstr = "raise " + _repr_strip(exc) + " from " + _repr_strip(cause)
        myglobals, mylocals = _get_caller_globals_and_locals()
        exec(execstr, myglobals, mylocals)
