"""
Provides FileStorage implementation for MongoDB GridFS.

This is useful for storing files inside a mongodb database.

"""
from __future__ import absolute_import

from datetime import datetime
from pymongo import MongoClient
import gridfs
from bson import ObjectId

from .interfaces import FileStorage, StoredFile
from . import utils


class GridFSStoredFile(StoredFile):
    def __init__(self, file_id, gridout):
        _check_file_id(file_id)
        self._gridout = gridout
        self._closed = False

        metadata_info = {'filename': gridout.filename,
                         'content_type': gridout.content_type,
                         'content_length': gridout.length,
                         'last_modified': None}

        try:
            last_modified = gridout.upload_date
            if last_modified:
                metadata_info['last_modified'] = last_modified
        except:
            pass

        super(GridFSStoredFile, self).__init__(file_id=file_id, **metadata_info)

    def read(self, n=-1):
        if self._closed:
            raise ValueError("cannot read from a closed file")

        return self._gridout.read(n)

    def close(self):
        self._closed = True
        self._gridout.close()

    @property
    def closed(self):
        return self._closed


class GridFSStorage(FileStorage):
    """:class:`depot.io.interfaces.FileStorage` implementation that stores files on MongoDB.

    All the files are stored using GridFS to the database pointed by the ``mongouri`` parameter into
    the collection named ``collection``.

    """
    def __init__(self, mongouri, collection='filedepot'):
        self._cli = MongoClient(mongouri)
        self._db = self._cli.get_default_database()
        self._gridfs = gridfs.GridFS(self._db, collection=collection)
        self._gridfs_bucket = gridfs.GridFSBucket(self._db, bucket_name=collection)

    def get(self, file_or_id):
        fileid = self.fileid(file_or_id)

        try:
            gridout = self._gridfs.get(_check_file_id(fileid))
        except gridfs.errors.NoFile:
            raise IOError('File %s not existing' % fileid)

        return GridFSStoredFile(fileid, gridout)

    def create(self, content, filename=None, content_type=None):
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        new_file_id = self._gridfs.put(content,
                                       filename=filename,
                                       content_type=content_type,
                                       last_modified=utils.timestamp())
        return str(new_file_id)

    def create_stream(self, filename=None, content_type=None):
        if not content_type:
            content_type = utils._FileInfo.DEFAULT_CONTENT_TYPE
        if not filename:
            filename = utils._FileInfo.DEFAULT_NAME

        metadata = {'contentType': content_type}
        stream = self._gridfs_bucket.open_upload_stream(filename, metadata=metadata)
        new_file_id = stream._id
        setattr(stream, 'file_id', str(new_file_id))

        return stream

    def replace(self, file_or_id, content, filename=None, content_type=None):
        fileid = self.fileid(file_or_id)
        fileid = _check_file_id(fileid)

        content, filename, content_type = self.fileinfo(content, filename, content_type,
                                                        lambda: self.get(fileid))

        self._gridfs.delete(fileid)
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

    def list(self):
        list_ids = []
        for filename in self._gridfs.list():
            list_ids.append(str(self._gridfs.find_one({"filename": filename})._id))
        return list_ids


def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        return ObjectId(file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)
