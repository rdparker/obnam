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


class Host(obnamlib.Object):

    """A host object."""

    kind = obnamlib.HOST

    def __init__(self, id):
        obnamlib.Object.__init__(self, id=id)
        self._genrefs = None
        self._maprefs = None

    def get_genrefs(self):
        if self._genrefs is None:
            list = self.extract(kind=obnamlib.GENREF)
            self._genrefs = [str(c) for c in list]
        return self._genrefs

    def set_genrefs(self, genrefs):
        self._genrefs = genrefs

    genrefs = property(get_genrefs, set_genrefs,
                       doc="References to GEN objects.")

    def get_maprefs(self):
        if self._maprefs is None:
            list = self.extract(kind=obnamlib.MAPREF)
            self._maprefs = [str(c) for c in list]
        return self._maprefs

    def set_maprefs(self, maprefs):
        self._maprefs = maprefs

    maprefs = property(get_maprefs, set_maprefs,
                       doc="References to MAP objects.")

    def prepare_for_encoding(self):
        if self._genrefs is not None:
            for genref in self._genrefs:
                c = obnamlib.GenRef(genref)
                self.components.append(c)
            self._genrefs = None
        if self._maprefs is not None:
            for mapref in self._maprefs:
                c = obnamlib.MapRef(mapref)
                self.components.append(c)
            self._maprefs = None

