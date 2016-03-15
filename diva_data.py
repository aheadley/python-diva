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
    ),
    Anchor('a_toc_start'),
    Struct('toc',
        Array(lambda ctx: ctx._.header.entry_count,
            Struct('entries',
                ULInt32('offset'),
                ULInt32('length'),
            ),
        ),
        ULInt32('metadata_offset'),
        ULInt32('metadata_length'),
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
            ),
        ),
    ),
)

ColumnTypeMap = {
    'TYPE_STRING'       : UBInt32('value'),
    'TYPE_DATA'         : UBInt64('value'),
    'TYPE_FLOAT'        : BFloat32('value'),
    'TYPE_8BYTE2'       : SBInt64('value'),
    'TYPE_8BYTE'        : SBInt64('value'),
    'TYPE_4BYTE2'       : SBInt32('value'),
    'TYPE_4BYTE'        : SBInt32('value'),
    'TYPE_2BYTE2'       : SBInt16('value'),
    'TYPE_2BYTE'        : SBInt16('value'),
    'TYPE_1BYTE2'       : Byte('value'),
    'TYPE_1BYTE'        : Byte('value'),
}

CPK_UTF_Table_ColumnType = Enum(Byte('column_type'),
    # STORAGE_MASK        = 0xF0,
    STORAGE_PERROW      = 0x50,
    STORAGE_CONSTANT    = 0x30,
    STORAGE_ZERO        = 0x10,

    # TYPE_MASK           = 0x0F,
    TYPE_DATA           = 0x0B,
    TYPE_STRING         = 0x0A,
    TYPE_FLOAT          = 0x08,
    TYPE_8BYTE2         = 0x07,
    TYPE_8BYTE          = 0x06,
    TYPE_4BYTE2         = 0x05,
    TYPE_4BYTE          = 0x04,
    TYPE_2BYTE2         = 0x03,
    TYPE_2BYTE          = 0x02,
    TYPE_1BYTE2         = 0x01,
    TYPE_1BYTE          = 0x00,

    # _default_           = 'TYPE_1BYTE',
)

ColumnTypeMapMirror = {v: ColumnTypeMap[k] for k, v in CPK_UTF_Table_ColumnType.encoding.iteritems() if k.startswith('TYPE_')}

UTF_STORAGE_MASK    = 0xF0
UTF_TYPE_MASK       = 0x0F

CPK_UTF_Table = Struct('utf_table',
    Anchor('a_table_offset'),
    Magic('@UTF'),
    Struct('table_info',
        SBInt32('size'),
        Anchor('a_offset_anchor'),
        # SBInt32('schema_offset'), # & 0x20 ?
        # Value('v_schema_offset', lambda ctx: 0x20),
        SBInt32('rows_offset'),
        SBInt32('strings_offset'),
        SBInt32('data_offset'),
        SBInt32('name_offset'),

        SBInt16('column_count'),
        SBInt16('row_width'),

        SBInt32('row_count'),

        Value('v_strings_size', lambda ctx: ctx.data_offset - ctx.strings_offset)
    ),

    Anchor('a_columns_offset'),

    Array(lambda ctx: ctx.table_info.column_count, Struct('column',
        Anchor('a_column_marker'),
        Value('v_column_id', lambda ctx: (ctx.a_column_marker - ctx._.a_columns_offset) / 5),

        Byte('column_type'),
        SBInt32('column_name_offset'),
        Pointer(lambda ctx: ctx._.table_info.a_offset_anchor + ctx._.table_info.strings_offset + ctx.column_name_offset,
            CString('column_name')),

        Value('v_type', lambda ctx: ctx.column_type & UTF_TYPE_MASK), # TYPE_MASK
        Value('v_storage', lambda ctx: ctx.column_type & UTF_STORAGE_MASK), # STORAGE_MASK
        If(lambda ctx: ctx.v_storage == 0x30, # STORAGE_CONSTANT
            Struct('column_offset',
                Anchor('a_constant_offset'),
                Switch('column_offset', lambda ctx: ctx.v_type,
                    ColumnTypeMap,
                ),
            ),
        ),
        Pointer(lambda ctx: ctx._.table_info.data_offset,
            Array(lambda ctx: ctx._.table_info.row_count, Struct('rows',
                Padding(lambda ctx: ctx._._.table_info.row_width),
                # Switch('value', lambda ctx: ctx,
                #     ColumnTypeMapMirror),
                # Padding(lambda ctx: ctx._._.table_info.row_width),
            ))
        ),
    )),
)

CPKFormat = Struct('CPK',
    Struct('header',
        Magic('CPK '),
        Padding(12),
    ),
    CPK_UTF_Table,
)

DSCFormat = Struct('DSC',


    Pass
)
