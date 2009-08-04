# Copyright (C) 2009  Lars Wirzenius <liw@liw.fi>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import obnamlib


class SigBlockSize(obnamlib.Component):

    def __init__(self, block_size):
        if type(block_size) == int:
            block_size = obnamlib.varint.encode(block_size)
        obnamlib.Component.__init__(self, kind=obnamlib.SIGBLOCKSIZE, 
                                    string=block_size)

    @property
    def block_size(self):
        return obnamlib.varint.decode(str(self), 0)[0]
