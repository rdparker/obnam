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


class SubFilePart(obnamlib.CompositeComponent):

    composite_kind = obnamlib.SUBFILEPART
    
    def __init__(self, children=None):
        obnamlib.CompositeComponent.__init__(self, children or [])

    def get_filepartref(self):
        return self.first_string(kind=obnamlib.FILEPARTREF)

    def set_filepartref(self, ref):
        self.extract(kind=obnamlib.FILEPARTREF)
        self.children += [obnamlib.FilePartRef(ref)]

    filepartref = property(get_filepartref, set_filepartref)
        
    def getint(self, kind):
        s = self.first_string(kind=kind)
        return obnamlib.varint.decode(s, 0)[0]
        
    def setint(self, kind, klass, value):
        self.extract(kind=kind)
        s = obnamlib.varint.encode(value)
        self.children += [klass(s)]
        
    def get_offset(self):
        return self.getint(obnamlib.OFFSET)
        
    def set_offset(self, offset):
        self.setint(obnamlib.OFFSET, obnamlib.Offset, offset)
        
    offset = property(get_offset, set_offset)
        
    def get_length(self):
        return self.getint(obnamlib.LENGTH)
        
    def set_length(self, length):
        self.setint(obnamlib.LENGTH, obnamlib.Length, length)
        
    length = property(get_length, set_length)
