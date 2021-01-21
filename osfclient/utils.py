"""Utility functions

Helpers and other assorted functions.
"""

import hashlib
import os
import six

KNOWN_PROVIDERS = ['osfstorage', 'github', 'figshare', 'googledrive', 'owncloud']


def norm_remote_path(path):
    """Normalize `path`.

    All remote paths are absolute.
    """
    path = os.path.normpath(path)
    if path.startswith(os.path.sep):
        return path[1:]
    else:
        return path


def split_storage(path, default='osfstorage'):
    """Extract storage name from file path.

    If a path begins with a known storage provider the name is removed
    from the path. Otherwise the `default` storage provider is returned
    and the path is not modified.
    """
    path = norm_remote_path(path)

    for provider in KNOWN_PROVIDERS:
        if path.startswith(provider + '/'):
            if six.PY3:
                return path.split('/', maxsplit=1)
            else:
                return path.split('/', 1)

    return (default, path)


def makedirs(path, mode=511, exist_ok=False):
    # mode 0777 is 511 in decimal
    if six.PY3:
        return os.makedirs(path, mode, exist_ok)
    else:
        if os.path.exists(path) and exist_ok:
            return None
        else:
            return os.makedirs(path, mode)


def file_empty(fp):
    """Determine if a file is empty or not."""
    # for python 2 we need to use a homemade peek()
    if six.PY2:
        contents = fp.read()
        fp.seek(0)
        return not bool(contents)

    else:
        return not fp.read()


def checksum(file_path, hash_type='md5', block_size=65536):
    """Returns either the md5 or sha256 hash of a file at `file_path`.
    
    md5 is the default hash_type as it is faster than sha256

    The default block size is 64 kb, which appears to be one of a few command
    choices according to https://stackoverflow.com/a/44873382/2680. The code
    below is an extension of the example presented in that post.
    """
    if hash_type == 'md5':
        hash_ = hashlib.md5()
    elif hash_type == 'sha256':
        hash_ = hashlib.sha256()
    else:
        raise ValueError(
            "{} is an invalid hash_type. Expected 'md5' or 'sha256'."
            .format(hash_type)
        )

    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hash_.update(block)
    return hash_.hexdigest()


def get_local_file_size(fp):
    """Get file size from file pointer"""
    # one-liner to get file size from file pointer explained at
    # https://stackoverflow.com/a/283719/2680824
    return os.fstat(fp.fileno()).st_size 
