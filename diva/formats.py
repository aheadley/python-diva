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

from .util import IsTimestamp, IsNotTimestamp, Dynamic

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
    'TYPE_STRING'       : SBInt32('value'),
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

ColumnTypeMapMirror = {v: ColumnTypeMap[k]
    for k, v in CPK_UTF_Table_ColumnType.encoding.iteritems()
        if k.startswith('TYPE_')}

UTF_STORAGE_MASK    = 0xF0
UTF_TYPE_MASK       = 0x0F

def build_utf_row(ctx):
    cell_types = ColumnTypeMapMirror.copy()
    cell_types[0x0B] = Struct('value',
        SBInt32('offset'),
        SBInt32('size'),
        # Pointer(lambda ctx: ctx.offset,
        #     # OnDemand(String('value', lambda ctx: ctx.size)),
        # ),
    )
    cell_types[0x0A] = Struct('value',
        SBInt32('offset'),
        Pointer(lambda ctx: ctx.offset + ctx._._.a_table_offset + 8 + ctx._._.table_info.strings_offset,
            CString('value')
            # OnDemand(CString('value'))
        ),
    )

    # cell_types[0x07] = Struct('value', Padding(4), SBInt32('value'))
    # cell_types[0x06] = Struct('value', Padding(4), SBInt32('value'))

    cells = []
    for col in ctx.columns:
        cell = cell_types[col.v_type]
        if col.v_storage == 0x10:
            cell = Value('zero', lambda ctx: 0x00)
        else:
            if col.v_storage == 0x30:
                cell = Pointer(lambda ctx: col.constant_offset.a_constant_offset, cell)
        cell = Rename(col.column_name, cell)
        cells.append(cell)

    return Struct('row', *cells)

CPK_UTF_Table = Struct('utf_table',
    Anchor('a_table_offset'),
    Magic('@UTF'),
    Struct('table_info',
        SBInt32('size'),
        Anchor('a_offset_anchor'),
        SBInt32('rows_offset'),
        SBInt32('strings_offset'),
        SBInt32('data_offset'),
        SBInt32('name_offset'),

        SBInt16('column_count'),
        SBInt16('row_size'),

        SBInt32('row_count'),

        Value('v_strings_size', lambda ctx: ctx.data_offset - ctx.strings_offset)
    ),

    Array(lambda ctx: ctx.table_info.column_count, Struct('columns',
        Byte('column_type'),
        SBInt32('column_name_offset'),
        Pointer(lambda ctx: ctx._.table_info.a_offset_anchor + ctx._.table_info.strings_offset + ctx.column_name_offset,
            CString('column_name')),

        Value('v_type', lambda ctx: ctx.column_type & UTF_TYPE_MASK), # TYPE_MASK
        Value('v_storage', lambda ctx: ctx.column_type & UTF_STORAGE_MASK), # STORAGE_MASK
        If(lambda ctx: ctx.v_storage == 0x30, # STORAGE_CONSTANT
            Struct('constant_offset',
                Anchor('a_constant_offset'),
                Switch('offset_value', lambda ctx: ctx._.v_type,
                    ColumnTypeMapMirror,
                ),
            ),
        ),
    )),

    Pointer(lambda ctx: ctx.a_table_offset + 8 + ctx.table_info.rows_offset,
        Array(lambda ctx: ctx.table_info.row_count, Dynamic('rows', build_utf_row)),
    ),
)

CPKFormat = Struct('CPK',
    Struct('header',
        Magic('CPK '),
        Padding(12),
        CPK_UTF_Table,
    ),

    IfThenElse('v_toc_offset', lambda ctx: ctx.header.utf_table.rows[0].TocOffset != 0,
        Value('_toc_offset', lambda ctx: ctx.header.utf_table.rows[0].TocOffset),
        Value('_itoc_offset', lambda ctx: ctx.header.utf_table.rows[0].ITocOffset),
    ),
    Value('v_content_offset', lambda ctx: ctx.header.utf_table.rows[0].ContentOffset),
    Value('v_file_count', lambda ctx: ctx.header.utf_table.rows[0].Files),
    Value('v_alignment', lambda ctx: ctx.header.utf_table.rows[0].Align),

    Pointer(lambda ctx: ctx.v_toc_offset, Struct('toc',
        Magic('TOC '),
        Padding(12),
        CPK_UTF_Table,
    )),
)

DSC_KeyStructs = {
    06: Struct('opt',
            SLInt32('large_value_06_00'),
            SLInt32('large_value_06_01'),
            SLInt32('zero_06_00'),
            SLInt32('large_value_06_02'),
            SLInt32('point_value_06_00'),
            SLInt32('small_value_06_00'),
        ),
    11: Struct('opt',
            SLInt32('small_value_11_00'),
            SLInt32('small_value_11_01'),
            SLInt32('zero_11_00'),
            SLInt32('small_value_11_02'),
            SLInt32('small_value_11_03'),
            SLInt32('small_value_11_04'),
        ),
    13: Select('try_13',
            # Struct('opt',
            #     SLInt32('small_value_13_00'),
            #     SLInt32('small_value_13_01'),
            #     SLInt32('small_value_13_02'),
            #     SLInt32('point_value_13_03'),
            #     SLInt32('small_value_13_04'),
            #     SLInt32('small_value_13_05'),
            #     SLInt32('small_value_13_06'),
            #     SLInt32('point_value_13_07'),
            # ),
            Struct('opt',
                SLInt32('small_value_13_00'),
                SLInt32('small_value_13_01'),
                SLInt32('small_value_13_02'),
                SLInt32('point_value_13_00'),
            ),
            # Struct('opt',
            #     SLInt32('zero_13_00'),
            # ),
        ),
    18: Struct('opt',
            SLInt32('point_value_18_00'),
        ),
    19: Struct('opt',
            SLInt32('point_value_19_00'),
        ),
    20: Struct('opt',
            SLInt32('zero_20_00'),
        ),
    21: Struct('opt',
            SLInt32('point_value_21_00'),
            SLInt32('point_value_21_01'),
        ),
    22: Struct('opt',
            Pass,
        ),
    24: Struct('opt',
            Pass,
        ),
}

DSCFormat = Struct('DSC',
    # Struct('header',
    #     Padding(4 * 46),
    #     Array(16, SLInt32('prefix_values')),
    # ),
    GreedyRange(IsNotTimestamp(SLInt32('prefix_values'))),
    GreedyRange(Struct('events',
        IsTimestamp(SLInt32('timestamp')),
        GreedyRange(IsNotTimestamp(SLInt32('other_data'))),
    )),
    # GreedyRange(Struct('keys',
    #     IsTimestamp(SLInt32('timestamp')),
    #     SLInt32('key_format'),
    #     SLInt32('small_value00'),
    #     Switch('format_switch', lambda ctx: ctx.key_format, DSC_KeyStructs),
    #     SLInt32('small_value01'),
    # )),
    Anchor('a_stopped_reading'),
    # GreedyRange(SLInt32('remaining_values')),
)
