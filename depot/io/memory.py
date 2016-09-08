"""
Provides MemoryStorage implementation to keep files in memory.

This is useful for caches or tests.

"""
import uuid
import io
from datetime import datetime

from .interfaces import FileStorage, StoredFile
from . import utils
from .._compat import unicode_text


class MemoryStoredFile(StoredFile):
    def __init__(self, files, file_id, file_data):
        _check_file_id(file_id)
        self._files = files
        self._files_key = file_id
        self._file = None
        super(MemoryStoredFile, self).__init__(file_id=file_id, **file_data['metadata'])

    def read(self, n=-1):
        if self._file is None:
            self._file = io.BytesIO(self._files[self._files_key]['data'])
        return self._file.read(n)

    def close(self):
        if self._file is None:
            self._file = io.BytesIO(self._files[self._files_key]['data'])
        self._file.close()

    @property
    def closed(self):
        if self._file is None:
            return False
        return self._file.closed


class MemoryFileStorage(FileStorage):
    """:class:`depot.io.interfaces.FileStorage` implementation that keeps files in memory.

    This is generally useful for caches and tests.
    """
    def __init__(self, **kwargs):
        self.files = {}

    def get(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        try:
            file_data = self.files[fileid]
        except KeyError:
            raise IOError('File %s not existing' % fileid)

        return MemoryStoredFile(self.files, fileid, file_data)

    def __save_file(self, file_id, content, filename, content_type=None):
        if hasattr(content, 'read'):
            data = content.read()
        else:
            if isinstance(content, unicode_text):
                raise TypeError('Only bytes can be stored, not unicode')
            data = content

        self.files[file_id] = {
            'data': data,
            'metadata': {
                'filename': filename or 'unknown',
                'content_type': content_type,
                'content_length': len(data),
                'last_modified': datetime.strptime(utils.timestamp(), '%Y-%m-%d %H:%M:%S')
            }
        }

    def create(self, content, filename=None, content_type=None):
        new_file_id = str(uuid.uuid1())
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        self.__save_file(new_file_id, content, filename, content_type)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        # First check file existed and we are not using replace
        # as a way to force a specific file id on creation.
        if fileid not in self.files:
            raise IOError('File %s not existing' % file_or_id)

        content, filename, content_type = self.fileinfo(content, filename, content_type,
                                                        lambda: self.get(fileid))

        self.delete(fileid)
        self.__save_file(fileid, content, filename, content_type)
        return fileid

    def delete(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)
        self.files.pop(fileid, None)

    def exists(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)
        return fileid in self.files

    def list(self):
        return list(self.files.keys())


def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        uuid.UUID('{%s}' % file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)
