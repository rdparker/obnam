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


import errno
import getpass
import logging
import os
import pwd
import stat
import urlparse

import paramiko

import obnamlib


class SftpFS(obnamlib.VirtualFileSystem):

    """A VFS implementation for SFTP."""

    def __init__(self, baseurl, progress):
        obnamlib.VirtualFileSystem.__init__(self, baseurl, progress)
        self.first_lutimes = True

    def connect(self):
        user = host = port = path = None
        scheme, netloc, path, query, fragment = urlparse.urlsplit(self.baseurl)
        assert scheme == "sftp", "wrong scheme in %s" % self.baseurl
        if "@" in netloc:
            user, netloc = netloc.split("@", 1)
        else:
            user = self.get_username()
        if "." in netloc:
            host, port = netloc.split(":", 1)
            port = int(port)
        else:
            host = netloc
            port = 22
        if path.startswith("/~/"):
            path = path[3:]
        self.basepath = path
        self.transport = paramiko.Transport((host, port))
        self.transport.connect()
        self.check_host_key(host)
        self.authenticate(user)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def get_username(self):
        return pwd.getpwuid(os.getuid()).pw_name

    def check_host_key(self, hostname):
        key = self.transport.get_remote_server_key()
        known_hosts = os.path.expanduser('~/.ssh/known_hosts')
        keys = paramiko.util.load_host_keys(known_hosts)
        if hostname not in keys:
            raise obnamlib.Exception("Host key for %s not found" % hostname)
        elif not keys[hostname].has_key(key.get_name()):
            raise obnamlib.Exception("Unknown host key for %s" % hostname)
        elif keys[hostname][key.get_name()] != key:
            print '*** WARNING: Host key has changed!!!'
            raise obnamlib.Exception("Host key has changed for %s" % hostname)
    
    def authenticate(self, username):
        if self.authenticate_via_agent(username):
            return
        raise obnamlib.Exception("Can't authenticate to SSH server.")

    def authenticate_via_agent(self, username):
        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        for key in agent_keys:
            try:
                self.transport.auth_publickey(username, key)
                return True
            except paramiko.SSHException:
                pass
        return False
    
    def close(self):
        self.transport.close()

    def join(self, relative_path):
        return os.path.join(self.basepath, relative_path.lstrip("/"))

    def listdir(self, relative_path):
        return self.sftp.listdir(self.join(relative_path))

    def lock(self, lockname):
        try:
            self.write_file(lockname, "")
        except IOError, e:
            if e.errno == errno.EEXIST:
                raise obnamlib.Exception("Lock %s already exists" % lockname)
            else:
                raise

    def unlock(self, lockname):
        if self.exists(lockname):
            self.remove(lockname)

    def remove(self, relative_path):
        self.sftp.remove(self.join(relative_path))

    def lstat(self, relative_path):
        return self.sftp.lstat(self.join(relative_path))

    def chmod(self, relative_path, mode):
        self.sftp.chmod(self.join(relative_path), mode)

    def lutimes(self, relative_path, atime, mtime):
        # FIXME: This does not work for symlinks!
        # Sftp does not have a way of doing that. This means if the restore
        # target is over sftp, symlinks and their targets will have wrong
        # mtimes.
        if self.first_lutimes:
            logging.warning("lutimes used over SFTP, this does not work "
                            "against symlinks (warning appears only first "
                            "time)")
            self.first_lutimes = False
        self.sftp.utime(self.join(relative_path), (atime, mtime))

    def link(self, existing, new):
        raise obnamlib.Exception("Cannot link on SFTP. Sorry.")

    def readlink(self, relative_path):
        return self.sftp.readlink(self.join(relative_path))

    def symlink(self, existing, new):
        self.sftp.symlink(existing, self.join(new))

    def open(self, relative_path, mode):
        return self.sftp.file(self.join(relative_path), mode)

    def exists(self, relative_path):
        try:
            self.lstat(relative_path)
            return True
        except IOError:
            return False

    def isdir(self, relative_path):
        try:
            st = self.lstat(relative_path)
        except IOError:
            return False
        return stat.S_ISDIR(st.st_mode)

    def mkdir(self, relative_path):
        self.sftp.mkdir(self.join(relative_path))

    def makedirs(self, relative_path):
        if self.isdir(relative_path):
            return
        parent = os.path.dirname(relative_path)
        if parent and parent != relative_path:
            self.makedirs(parent)
        self.mkdir(relative_path)

    def cat(self, relative_path):
        f = self.open(relative_path, "r")
        chunks = []
        while True:
            # 32 KiB is the chunk size that gives me the fastest speed
            # for sftp transfers. I don't know why the size matters.
            chunk = f.read(32 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        f.close()
        return "".join(chunks)

    def write_file(self, relative_path, contents):
        self.makedirs(os.path.dirname(relative_path))
        f = self.open(relative_path, 'wx')
        f.write(contents)
        f.close()

    def overwrite_file(self, relative_path, contents):
        self.makedirs(os.path.dirname(relative_path))
        f = self.open(relative_path, 'w')
        f.write(contents)
        f.close()