"""
Provides FileStorage implementation for MongoDB GridFS.

This is useful for storing files inside a mongodb database.

"""
from __future__ import absolute_import

from datetime import datetime
import uuid
from boto.s3.connection import S3Connection
from depot._compat import unicode_text

from .interfaces import FileStorage, StoredFile
from . import utils


class S3StoredFile(StoredFile):
    def __init__(self, file_id, key):
        _check_file_id(file_id)
        self._key = key

        metadata_info = {'filename': key.get_metadata('x-depot-filename'),
                         'content_type': key.content_type,
                         'content_length': key.size,
                         'last_modified': None}

        try:
            last_modified = key.get_metadata('x-depot-modified')
            if last_modified:
                metadata_info['last_modified'] = datetime.strptime(last_modified,
                                                                   '%Y-%m-%d %H:%M:%S')
        except:
            pass

        super(S3StoredFile, self).__init__(file_id=file_id, **metadata_info)

    def read(self, n=-1):
        if self.closed:
            raise ValueError("cannot read from a closed file")

        return self._key.read(n)

    def close(self):
        self._key.close()

    @property
    def closed(self):
        return self._key.closed

    @property
    def public_url(self):
        return self._key.generate_url(expires_in=0, query_auth=False)


class S3Storage(FileStorage):
    """:class:`depot.io.interfaces.FileStorage` implementation that stores files on S3.

    All the files are stored inside a bucket named ``bucket`` to which Depot connects
    to using ``access_key_id`` and ``secret_access_key``.

    """

    def __init__(self, access_key_id, secret_access_key, bucket=None):
        if bucket is None:
            bucket = 'filedepot-%s' % (access_key_id.lower(),)

        self._conn = S3Connection(access_key_id, secret_access_key)
        self._bucket = self._conn.lookup(bucket)
        if self._bucket is None:
            self._bucket = self._conn.create_bucket(bucket)

    def get(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        key = self._bucket.get_key(fileid)
        if key is None:
            raise IOError('File %s not existing' % fileid)

        return S3StoredFile(fileid, key)

    def __save_file(self, key, content, filename, content_type=None):
        key.set_metadata('content-type', content_type)
        key.set_metadata('x-depot-filename', filename)
        key.set_metadata('x-depot-modified', utils.timestamp())
        key.set_metadata('Content-Disposition', 'inline; filename="%s"' % filename)

        if hasattr(content, 'read'):
            can_seek_and_tell = True
            try:
                pos = content.tell()
                content.seek(pos)
            except:
                can_seek_and_tell = False

            if can_seek_and_tell:
                key.set_contents_from_file(content, policy='public-read')
            else:
                key.set_contents_from_string(content.read(), policy='public-read')
        else:
            if isinstance(content, unicode_text):
                raise TypeError('Only bytes can be stored, not unicode')
            key.set_contents_from_string(content, policy='public-read')

    def create(self, content, filename=None, content_type=None):
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        new_file_id = str(uuid.uuid1())
        key = self._bucket.new_key(new_file_id)
        self.__save_file(key, content, filename, content_type)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        content, filename, content_type = self.fileinfo(content, filename, content_type)
        if filename is None:
            f = self.get(fileid)
            filename = f.filename
            content_type = f.content_type

        key = self._bucket.get_key(fileid)
        self.__save_file(key, content, filename, content_type)
        return fileid

    def delete(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        k = self._bucket.get_key(fileid)
        if k:
            k.delete()

    def exists(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        k = self._bucket.get_key(fileid)
        return k is not None


def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        uuid.UUID('{%s}' % file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)
