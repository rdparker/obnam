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


import stat
import unittest

import mox

import obnamlib


class DummyObject(object):

    """Dummy object for aiding in some unit tests."""

    def __init__(self, id):
        self.id = id


class BackupCommandTests(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.cmd = obnamlib.BackupCommand()
        self.cmd.store = self.mox.CreateMock(obnamlib.Store)
        self.cmd.fs = self.mox.CreateMock(obnamlib.VirtualFileSystem)

    def test_backs_up_new_symlink_correctly(self):
        st = obnamlib.make_stat()
        self.cmd.fs.readlink("foo").AndReturn("target")
        self.mox.ReplayAll()
        symlink = self.cmd.backup_new_symlink("foo", st)
        self.mox.VerifyAll()
        self.assertEqual(symlink.filename, "foo")
        self.assertEqual(symlink.stat, st)
        self.assertEqual(symlink.symlink_target, "target")

    def test_backs_up_new_file_correctly(self):
        st = obnamlib.make_stat()

        f = self.mox.CreateMock(file)
        fc = self.mox.CreateMock(obnamlib.FileContents)
        fc.id = "contentsid"

        self.cmd.fs.open("foo", "r").AndReturn(f)
        self.cmd.store.put_contents(f, self.cmd.PART_SIZE).AndReturn(fc)
        f.close()

        self.mox.ReplayAll()
        new_file = self.cmd.backup_new_file("foo", st)
        self.mox.VerifyAll()
        self.assertEqual(new_file.filename, "foo")
        self.assertEqual(new_file.stat, st)
        self.assertEqual(new_file.contref, fc.id)
        self.assertEqual(new_file.sigref, None)
        self.assertEqual(new_file.deltaref, None)

    def test_backs_up_filegroups_correctly(self):
        fg = self.mox.CreateMock(obnamlib.FileGroup)
        fg.components = self.mox.CreateMock(list)

        # First create FileGroup.
        self.cmd.store.new_object(kind=obnamlib.FILEGROUP).AndReturn(fg)
        
        # Backup foo, a regular file.
        self.cmd.fs.lstat("foo").AndReturn(
            obnamlib.make_stat(st_mode=stat.S_IFREG))
        f = self.mox.CreateMock(file)
        self.cmd.fs.open("foo", "r").AndReturn(f)
        cont = self.mox.CreateMock(obnamlib.FileContents)
        cont.id = "filecontents.id"
        self.cmd.store.put_contents(f, self.cmd.PART_SIZE).AndReturn(cont)
        f.close()
        fg.components.append(mox.IsA(obnamlib.Component))
        
        # Backup bar, a symlink.
        self.cmd.fs.lstat("bar").AndReturn(
            obnamlib.make_stat(st_mode=stat.S_IFLNK))
        self.cmd.fs.readlink("bar").AndReturn("target")
        fg.components.append(mox.IsA(obnamlib.Component))
        
        # Backup foobar, something else.
        self.cmd.fs.lstat("foobar").AndReturn(obnamlib.make_stat())
        fg.components.append(mox.IsA(obnamlib.Component))
        
        # Put FileGroup in store.
        self.cmd.store.put_object(fg)        

        self.mox.ReplayAll()
        ret = self.cmd.backup_new_files_as_groups(["foo", "bar", "foobar"])
        self.mox.VerifyAll()
        self.assertEqual(ret, [fg])

    def test_backs_up_directory_correctly(self):
        filenames = []
        def mock_backup_files(names):
            for name in names:
                filenames.append(name)
            return [DummyObject("fg")]
        self.cmd.backup_new_files_as_groups = mock_backup_files

        dir = self.mox.CreateMock(obnamlib.Dir)
        subdirs = [DummyObject(id) for id in ["dir1", "dir2"]]

        self.cmd.store.new_object(obnamlib.DIR).AndReturn(dir)
        self.cmd.store.put_object(dir)

        self.mox.ReplayAll()
        lstat = lambda *args: obnamlib.make_stat(st_mode=1, st_uid=2)
        ret = self.cmd.backup_dir("foo", subdirs, ["file1", "file2"],
                                  lstat=lstat)
        self.mox.VerifyAll()
        self.assertEqual(ret, dir)
        self.assertEqual(ret.name, "foo")
        self.assertEqual(ret.stat, obnamlib.make_stat(st_mode=1, st_uid=2))
        self.assertEqual(ret.dirrefs, ["dir1", "dir2"])
        self.assertEqual(ret.fgrefs, ["fg"])
        self.assertEqual(filenames, ["foo/file1", "foo/file2"])

    def test_backs_up_empty_directory_correctly(self):
        self.cmd.backup_new_files_as_groups = lambda: None

        lstat = lambda *args: obnamlib.make_stat()
        ret = self.cmd.backup_dir("foo", [], [], lstat=lstat)
        self.assertNotEqual(ret.stat, None)
        self.assertEqual(ret.dirrefs, [])
        self.assertEqual(ret.fgrefs, [])

    def test_backs_up_recursively_empty_directory_correctly(self):
        dir = self.mox.CreateMock(obnamlib.Dir)
        dir.id = "dirid"
        self.cmd.backup_dir = lambda *args: dir
        self.cmd.fs = self.mox.CreateMock(obnamlib.VirtualFileSystem)

        self.cmd.fs.depth_first("foo").AndReturn([("foo", [], [])])

        self.mox.ReplayAll()
        ret = self.cmd.backup_recursively("foo")
        self.mox.VerifyAll()
        self.assertEquals(ret, dir)

    def test_backs_up_recursively_non_empty_directory_correctly(self):
        args = []
        results = []
        self.count = 0
        def mock_backup_dir(dirname, subdirs, filenames):
            args.append((dirname, subdirs, filenames))
            self.count += 1
            dir = obnamlib.Dir(id=("%s" % self.count), name=dirname)
            results.append(dir)
            return dir
        self.cmd.backup_dir = mock_backup_dir

        tree = [
            ("foo/dir1", [], ["file2"]),
            ("foo", ["dir1"], ["file1"]),
            ]
        self.cmd.fs = self.mox.CreateMock(obnamlib.VirtualFileSystem)
        self.cmd.fs.depth_first("foo").AndReturn(tree)

        self.mox.ReplayAll()
        ret = self.cmd.backup_recursively("foo")
        self.mox.VerifyAll()
        self.assertEquals(ret, results[-1])
        self.assertEquals(args, 
                          [("foo/dir1", [], ["file2"]),
                           ("foo", [results[0]], ["file1"]),
                           ])

    def test_backs_up_mixed_roots(self):
        self.count = 0

        dirnames = []
        dirrefs = []
        def dummy_backup_recursively(dirname):
            dirnames.append(dirname)
            self.count += 1
            dir = obnamlib.Dir(id="%s" % self.count)
            dirrefs.append(dir.id)
            return dir
        self.cmd.backup_recursively = dummy_backup_recursively

        filenames = []
        fgrefs = []
        def dummy_backup_groups(names):
            for name in names:
                filenames.append(name)
            self.count += 1
            fg = obnamlib.FileGroup(id="%s" % self.count)
            fgrefs.append(fg.id)
            return [fg]
        self.cmd.backup_new_files_as_groups = dummy_backup_groups

        gen = self.mox.CreateMock(obnamlib.Generation)
        gen.dirrefs = []
        gen.fgrefs = []
        self.cmd.store.new_object(obnamlib.GEN).AndReturn(gen)
        self.cmd.fs.isdir("dir").AndReturn(True)
        self.cmd.fs.isdir("file").AndReturn(False)
        self.cmd.store.put_object(gen)
        
        self.mox.ReplayAll()
        gen = self.cmd.backup_generation(["dir", "file"])
        self.mox.VerifyAll()
        self.assertEqual(dirnames, ["dir"])
        self.assertEqual(filenames, ["file"])
        self.assertEqual(len(dirrefs), 1)
        self.assertEqual(len(fgrefs), 1)
        self.assertEqual(gen.dirrefs, dirrefs)
        self.assertEqual(gen.fgrefs, fgrefs)

    def test_backs_up_correctly(self):
        def mock_backup_generation(roots):
            return DummyObject("genid")
        self.cmd.backup_generation = mock_backup_generation

        host = self.mox.CreateMock(obnamlib.Host)
        host.genrefs = []

        self.cmd.store.get_host("foo").AndReturn(host)
        self.cmd.store.commit(host)

        self.mox.ReplayAll()
        self.cmd.backup("foo", ["bar", "foobar"])
        self.mox.VerifyAll()
        self.assertEqual(host.genrefs, ["genid"])