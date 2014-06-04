"""
Provides FileStorage implementation for MongoDB GridFS.

This is useful for storing files inside a mongodb database.

"""
from __future__ import absolute_import

import mimetypes
from datetime import datetime
import gridfs
from bson import ObjectId

from .interfaces import FileStorage, StoredFile
from . import utils


class GridFSStoredFile(StoredFile):
    def __init__(self, file_id, gridout):
        _check_file_id(file_id)
        self._gridout = gridout

        metadata_info = {'filename': gridout.filename,
                         'content_type': gridout.content_type,
                         'last_modified': None}

        try:
            last_modified = gridout.last_modified
            if last_modified:
                metadata_info['last_modified'] = datetime.strptime(last_modified,
                                                                   '%Y-%m-%d %H:%M:%S')
        except:
            pass

        super(GridFSStoredFile, self).__init__(file_id=file_id, **metadata_info)

    def read(self, n=-1):
        return self._gridout.read(n)


class GridFSStorage(FileStorage):
    def __init__(self, gridfs):
        self._gridfs = gridfs

    def get(self, file_or_id):
        fileid = self.fileid(file_or_id)

        try:
            gridout = self._gridfs.get(_check_file_id(fileid))
        except gridfs.errors.NoFile:
            raise IOError('File %s not existing' % fileid)

        return GridFSStoredFile(fileid, gridout)

    def create(self, content, filename, content_type=None):
        if content_type is None:
            guessed_type = mimetypes.guess_type(filename, strict=False)[0]
            content_type = guessed_type or 'application/octet-stream'

        new_file_id = self._gridfs.put(content,
                                       filename=filename,
                                       content_type=content_type,
                                       last_modified=utils.timestamp())
        return str(new_file_id)

    def replace(self, file_or_id, content, filename=None, content_type=None):
        fileid = self.fileid(file_or_id)
        fileid = _check_file_id(fileid)

        if filename is None:
            filename = self.get(fileid).filename

        self._gridfs.delete(fileid)

        if content_type is None:
            guessed_type = mimetypes.guess_type(filename, strict=False)[0]
            content_type = guessed_type or 'application/octet-stream'

        new_file_id = self._gridfs.put(content, _id=fileid,
                                       filename=filename,
                                       content_type=content_type,
                                       last_modified=utils.timestamp())
        return str(new_file_id)

    def delete(self, file_or_id):
        fileid = self.fileid(file_or_id)
        fileid = _check_file_id(fileid)
        self._gridfs.delete(fileid)

    def exists(self, file_or_id):
        fileid = self.fileid(file_or_id)
        fileid = _check_file_id(fileid)
        return self._gridfs.exists(fileid)


def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        return ObjectId(file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)
