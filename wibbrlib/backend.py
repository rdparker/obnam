"""Wibbr backend for communicating with the backup server.

This implementation only stores the stuff locally, however.

"""


import os

import uuid
import wibbrlib.cache


class LocalBackEnd:

    def __init__(self):
        self.local_root = None
        self.cache = None
        self.curdir = None


def init(config, cache):
    """Initialize the subsystem and return an opaque backend object"""
    be = LocalBackEnd()
    be.local_root = config.get("wibbr", "local-store")
    be.cache = cache
    be.curdir = str(uuid.uuid4())
    return be


def generate_block_id(be):
    """Generate a new identifier for the block, when stored remotely"""
    return os.path.join(be.curdir, str(uuid.uuid4()))


def _block_remote_pathname(be, block_id):
    """Return pathname on server for a given block id"""
    return os.path.join(be.local_root, block_id)


def upload(be, block_id, block):
    """Start the upload of a block to the remote server"""
    curdir_full = os.path.join(be.local_root, be.curdir)
    if not os.path.isdir(curdir_full):
        os.makedirs(curdir_full, 0700)
    f = file(_block_remote_pathname(be, block_id), "w")
    f.write(block)
    f.close()
    return None


def download(be, block_id):
    """Download a block from the remote server
    
    Return exception for error, or None for OK.
    
    """

    try:
        f = file(_block_remote_pathname(be, block_id), "r")
        block = f.read()
        f.close()
        wibbrlib.cache.put_block(be.cache, block_id, block)
    except IOError, e:
        return e
    return None


def list(be):
    """Return list of all files on the remote server"""
    list = []
    for dirpath, _, filenames in os.walk(be.local_root):
        list += [os.path.join(dirpath, x) for x in filenames]
    return list
