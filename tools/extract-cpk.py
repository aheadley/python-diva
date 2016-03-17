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

import logging
import os.path

from diva.formats import CPKFormat

logging.basicConfig(level=logging.DEBUG)

def extract_cpk_file(src_file, dest_dir):
    logging.info('Extracting CPK file: %s', src_file)
    with open(src_file) as src_handle:
        src_data = CPKFormat.parse_stream(src_handle)

        logging.info('Found %d entries', src_data.toc.utf_table.table_info.row_count)
        for i, entry in enumerate(src_data.toc.utf_table.rows):
            fn = entry.FileName.value
            if entry.DirName.value != '<NULL>':
                fn = os.path.join(entry.DirName.value, fn)
            dest_file = os.path.join(dest_dir, fn)
            logging.info('Extracting "%s" -> "%s" [%08d b]',
                fn, dest_file, entry.FileSize)
            with open(dest_file, 'w') as dest_handle:
                src_handle.seek(entry.FileOffset)
                dest_handle.write(src_handle.read(entry.FileSize))


if __name__ == '__main__':
    import sys

    extract_cpk_file(sys.argv[1], sys.argv[2])
