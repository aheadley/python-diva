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

from construct import *

AFSFormat = Struct('AFS',
    Struct('header',
        Magic('AFS\x00'),
        ULInt32('entry_count'),

        Pass
    ),
    Anchor('a_toc_start'),
    Struct('toc',
        Array(lambda ctx: ctx._.header.entry_count,
            Struct('entries',
                ULInt32('offset'),
                ULInt32('length'),

                Pass
            )
        ),
        ULInt32('metadata_offset'),
        ULInt32('metadata_length'),

        Pass
    ),
    Anchor('a_toc_end'),

    Pointer(lambda ctx: ctx.toc.metadata_offset,
        Array(lambda ctx: ctx.header.entry_count,
            Struct('metadata',
                String('name', 32, padchar='\x00'),
                ULInt16('year'),
                ULInt16('month'),
                ULInt16('day'),
                ULInt16('hour'),
                ULInt16('minute'),
                ULInt16('second'),
                ULInt32('length'),

                Pass
            )
        )
    ),

    Pass
)

DSCFormat = Struct('DSC',


    Pass
)
