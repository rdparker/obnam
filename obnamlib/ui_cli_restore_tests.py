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


import os
import stat
import unittest

import mox

import obnamlib


class RestoreCommandTests(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.cmd = obnamlib.RestoreCommand()

    def test_helper_restores_file_contents(self):
        fs = self.mox.CreateMock(obnamlib.VirtualFileSystem)
        f = self.mox.CreateMock(file)
        store = self.mox.CreateMock(obnamlib.Store)
        
        self.cmd.vfs = fs
        self.cmd.store = store
        self.cmd.host = "host"
        
        st = obnamlib.make_stat(st_mode=stat.S_IFREG | 0666, st_mtime=1,
                                st_atime=2, st_nlink=1)

        fs.open("foo", "w").AndReturn(f)
        store.cat("host", f, "contref", "deltaref")
        f.close()
        fs.chmod("foo", st.st_mode)
        fs.utime("foo", st.st_atime, st.st_mtime)
        
        self.mox.ReplayAll()
        self.cmd.restore_helper("foo", st, "contref", "deltaref", "target")
        self.mox.VerifyAll()

    def test_helper_restores_symlink(self):
        st = obnamlib.make_stat(st_mode=stat.S_IFLNK)
        self.cmd.vfs = self.mox.CreateMock(obnamlib.VirtualFileSystem)
        self.cmd.vfs.symlink("target", "foo")
        self.mox.ReplayAll()
        self.cmd.restore_helper("foo", st, "contref", "deltaref", "target")
        self.mox.VerifyAll()

    def mock_helper(self, filename, st, contref, deltaref, target):
        self.filename = filename
        self.st = st
        self.contref = contref
        self.deltaref = deltaref
        self.target = target

    def test_restore_file_calls_helper_correctly(self):
        st = obnamlib.make_stat()
        file = obnamlib.File("filename", st, "contref", None, "deltaref")

        self.mox.ReplayAll()
        self.cmd.restore_helper = self.mock_helper
        self.cmd.restore_file("dirname", file)
        self.mox.VerifyAll()
        self.assertEqual(self.filename, "dirname/filename")
        self.assertEqual(self.st, st)
        self.assertEqual(self.contref, "contref")
        self.assertEqual(self.deltaref, "deltaref")

    def mock_restore_file(self, dirname, file):
        self.dirname = dirname
        self.file = file

    def test_restore_generation_calls_restore_file_correctly(self):
        walker = self.mox.CreateMock(obnamlib.StoreWalker)
        cmd = obnamlib.RestoreCommand()
        cmd.vfs = self.mox.CreateMock(obnamlib.VirtualFileSystem)
        cmd.restore_file = self.mock_restore_file
        cmd.lookupper = self.mox.CreateMock(obnamlib.Lookupper)
        
        walker.walk_generation().AndReturn([("dirname", [], ["file"])])
        cmd.vfs.mkdir("dirname")
        dir = self.mox.CreateMock(obnamlib.Dir)
        dir.stat = obnamlib.make_stat()
        cmd.lookupper.get_dir('dirname').AndReturn(dir)
        cmd.vfs.chmod('dirname', 0)
        cmd.vfs.utime('dirname', 0, 0)

        self.mox.ReplayAll()
        cmd.restore_generation(walker)
        self.mox.VerifyAll()
        
        self.assertEqual(self.dirname, "dirname")
        self.assertEqual(self.file, "file")

    def test_restore_filename_calls_helper_correctly(self):
        lookupper = self.mox.CreateMock(obnamlib.Lookupper)
        vfs = self.mox.CreateMock(obnamlib.VirtualFileSystem)
        
        cmd = obnamlib.RestoreCommand()
        cmd.vfs = vfs
        cmd.restore_helper = self.mock_helper
        
        lookupper.get_file("foo/bar").AndReturn(("st", "contref", 
                                                 "sigref", "deltaref",
                                                 "target"))
        cmd.vfs.makedirs("foo")
        
        self.mox.ReplayAll()
        cmd.restore_filename(lookupper, "foo/bar")
        self.mox.VerifyAll()
        self.assertEqual(self.filename, "foo/bar")
        self.assertEqual(self.st, "st")
        self.assertEqual(self.contref, "contref")
        self.assertEqual(self.deltaref, "deltaref")

    def test_restore_dir_calls_restore_file_correctly(self):
        walker = self.mox.CreateMock(obnamlib.StoreWalker)
        cmd = obnamlib.RestoreCommand()
        cmd.vfs = self.mox.CreateMock(obnamlib.VirtualFileSystem)
        cmd.restore_file = self.mock_restore_file
        cmd.lookupper = self.mox.CreateMock(obnamlib.Lookupper)
        
        walker.walk("dirname").AndReturn([("dirname", [], ["file"])])
        cmd.vfs.mkdir("dirname")
        dir = self.mox.CreateMock(obnamlib.Dir)
        dir.stat = obnamlib.make_stat()
        cmd.lookupper.get_dir('dirname').AndReturn(dir)
        cmd.vfs.chmod('dirname', 0)
        cmd.vfs.utime('dirname', 0, 0)

        self.mox.ReplayAll()
        cmd.restore_dir(walker, "dirname")
        self.mox.VerifyAll()
        
        self.assertEqual(self.dirname, "dirname")
        self.assertEqual(self.file, "file")