# -*- coding: utf-8 -*-
import os
import errno
import tempfile
from hashlib import md5
from time import time
try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

from cachelib.base import BaseCache
from cachelib._compat import text_type


class FileSystemCache(BaseCache):

    """A cache that stores the items on the file system.  This cache depends
    on being the only user of the `cache_dir`.  Make absolutely sure that
    nobody but this cache stores files there or otherwise the cache will
    randomly delete files therein.

    :param cache_dir: the directory where cache files are stored.
    :param threshold: the maximum number of items the cache stores before
                      it starts deleting some. A threshold value of 0
                      indicates no threshold.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    :param mode: the file mode wanted for the cache files, default 0600
    """

    #: used for temporary files by the FileSystemCache
    _fs_transaction_suffix = '.__wz_cache'
    #: keep amount of files in a cache element
    _fs_count_file = '__wz_cache_count'

    def __init__(self, cache_dir, threshold=500, default_timeout=300,
                 mode=0o600):
        BaseCache.__init__(self, default_timeout)
        self._path = cache_dir
        self._threshold = threshold
        self._mode = mode

        try:
            os.makedirs(self._path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

        # If there are many files and a zero threshold,
        # the list_dir can slow initialisation massively
        if self._threshold != 0:
            self._update_count(value=len(self._list_dir()))

    @property
    def _file_count(self):
        return self.get(self._fs_count_file) or 0

    def _update_count(self, delta=None, value=None):
        # If we have no threshold, don't count files
        if self._threshold == 0:
            return

        if delta:
            new_count = self._file_count + delta
        else:
            new_count = value or 0
        self.set(self._fs_count_file, new_count, mgmt_element=True)

    def _normalize_timeout(self, timeout):
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout != 0:
            timeout = time() + timeout
        return int(timeout)

    def _list_dir(self):
        """return a list of (fully qualified) cache filenames
        """
        mgmt_files = [self._get_filename(name).split('/')[-1]
                      for name in (self._fs_count_file,)]
        return [os.path.join(self._path, fn) for fn in os.listdir(self._path)
                if not fn.endswith(self._fs_transaction_suffix)
                and fn not in mgmt_files]

    def _prune(self):
        if self._threshold == 0 or not self._file_count > self._threshold:
            return

        entries = self._list_dir()
        now = time()
        for idx, fname in enumerate(entries):
            try:
                remove = False
                with open(fname, 'rb') as f:
                    expires = pickle.load(f)
                remove = (expires != 0 and expires <= now) or idx % 3 == 0

                if remove:
                    os.remove(fname)
            except (IOError, OSError):
                pass
        self._update_count(value=len(self._list_dir()))

    def clear(self):
        for fname in self._list_dir():
            try:
                os.remove(fname)
            except (IOError, OSError):
                self._update_count(value=len(self._list_dir()))
                return False
        self._update_count(value=0)
        return True

    def _get_filename(self, key):
        if isinstance(key, text_type):
            key = key.encode('utf-8')  # XXX unicode review
        hash = md5(key).hexdigest()
        return os.path.join(self._path, hash)

    def get(self, key):
        filename = self._get_filename(key)
        try:
            with open(filename, 'rb') as f:
                pickle_time = pickle.load(f)
                if pickle_time == 0 or pickle_time >= time():
                    return pickle.load(f)
                else:
                    os.remove(filename)
                    return None
        except (IOError, OSError, pickle.PickleError):
            return None

    def add(self, key, value, timeout=None):
        filename = self._get_filename(key)
        if not os.path.exists(filename):
            return self.set(key, value, timeout)
        return False

    def set(self, key, value, timeout=None, mgmt_element=False):
        # Management elements have no timeout
        if mgmt_element:
            timeout = 0

        # Don't prune on management element update, to avoid loop
        else:
            self._prune()

        timeout = self._normalize_timeout(timeout)
        filename = self._get_filename(key)
        try:
            fd, tmp = tempfile.mkstemp(suffix=self._fs_transaction_suffix,
                                       dir=self._path)
            with os.fdopen(fd, 'wb') as f:
                pickle.dump(timeout, f, 1)
                pickle.dump(value, f, pickle.HIGHEST_PROTOCOL)

            os.rename(tmp, filename)
            os.chmod(filename, self._mode)
        except (IOError, OSError):
            return False
        else:
            # Management elements should not count towards threshold
            if not mgmt_element:
                self._update_count(delta=1)
            return True

    def delete(self, key, mgmt_element=False):
        try:
            os.remove(self._get_filename(key))
        except (IOError, OSError):
            return False
        else:
            # Management elements should not count towards threshold
            if not mgmt_element:
                self._update_count(delta=-1)
            return True

    def has(self, key):
        filename = self._get_filename(key)
        try:
            with open(filename, 'rb') as f:
                pickle_time = pickle.load(f)
                if pickle_time == 0 or pickle_time >= time():
                    return True
                else:
                    os.remove(filename)
                    return False
        except (IOError, OSError, pickle.PickleError):
            return False


