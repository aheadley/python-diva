#!/bin/env python2
# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2015 Alex Headley <aheadley@waysaboutstuff.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from construct import Construct, Validator

class Dynamic(Construct):
   """
   Dynamically creates a construct and uses it for parsing and building.
   This allows you to create change the construction tree on the fly.
   Deprecated.

   Parameters:
   * name - the name of the construct
   * factoryfunc - a function that takes the context and returns a new
     construct object which will be used for parsing and building.

   Example:
   def factory(ctx):
       if ctx.bar == 8:
           return UBInt8("spam")
       if ctx.bar == 9:
           return String("spam", 9)

   Struct("foo",
       UBInt8("bar"),
       Dynamic("spam", factory),
   )
   """
   __slots__ = ["factoryfunc"]
   def __init__(self, name, factoryfunc):
       Construct.__init__(self, name, self.FLAG_COPY_CONTEXT)
       self.factoryfunc = factoryfunc
       self._set_flag(self.FLAG_DYNAMIC)
   def _parse(self, stream, context):
       return self.factoryfunc(context)._parse(stream, context)
   def _build(self, obj, stream, context):
       return self.factoryfunc(context)._build(obj, stream, context)
   def _sizeof(self, context):
       return self.factoryfunc(context)._sizeof(context)

TIMESTAMP_THRESHOLD = 1000000
class IsTimestamp(Validator):
    def _validate(self, obj, context):
        return obj > TIMESTAMP_THRESHOLD

class IsNotTimestamp(Validator):
    def _validate(self, obj, context):
        return obj < TIMESTAMP_THRESHOLD
