# Copyright (C) 2008  Lars Wirzenius <liw@liw.fi>
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


class Generation(obnamlib.Object):

    """A backup generation."""

    kind = obnamlib.GEN

    def __init__(self, id):
        obnamlib.Object.__init__(self, id=id)
        self.dirrefs = []
        self.fgrefs = []

    def prepare_for_encoding(self):
        self.components += [obnamlib.DirRef(x) for x in self.dirrefs]
        self.components += [obnamlib.FileGroupRef(x) for x in self.fgrefs]

    def post_decoding_hook(self):
        self.dirrefs = self.extract_strings(kind=obnamlib.DIRREF)
        self.fgrefs = self.extract_strings(kind=obnamlib.FILEGROUPREF)