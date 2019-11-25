"""
Provides FileStorage implementation for Amazon S3.

This is useful for storing files in S3.

"""
from __future__ import absolute_import

from datetime import datetime
import uuid
from boto.s3.connection import S3Connection
from depot._compat import unicode_text, percent_encode, percent_decode
from depot.utils import make_content_disposition

from .interfaces import FileStorage, StoredFile
from . import utils

CANNED_ACL_PUBLIC_READ = 'public-read'
CANNED_ACL_PRIVATE = 'private'


class S3StoredFile(StoredFile):
    def __init__(self, file_id, key):
        _check_file_id(file_id)
        self._key = key
        filename = key.metadata.get('x-depot-filename')
        if filename:
            filename = percent_decode(filename)
        metadata_info = {'filename': filename,
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

        if n <= 0:
            n = 0
        return self._key.read(n)

    def close(self):
        self._key.close()

    @property
    def closed(self):
        return self._key.closed

    @property
    def public_url(self):
        # Old boto versions did support never.
        # but latests seems not to https://github.com/boto/boto/blob/develop/boto/s3/connection.py#L390
        expires_in = 31536000 # 1 YEAR
        return self._key.generate_url(expires_in=expires_in, query_auth=False)


class BucketDriver(object):

    def __init__(self, bucket, prefix):
        self.bucket = bucket
        self.prefix = prefix

    def get_key(self, key_name):
        return self.bucket.get_key('%s%s' % (self.prefix, key_name))

    def new_key(self, key_name):
        return self.bucket.new_key('%s%s' % (self.prefix, key_name))

    def list_key_names(self):
        keys = self.bucket.list(prefix=self.prefix)
        return [k.name[len(self.prefix):] for k in keys]


class S3Storage(FileStorage):
    """:class:`depot.io.interfaces.FileStorage` implementation that stores files on S3.

    **This is a version implemented on boto**
    Installing ``boto`` as a dependency is required to use this.

    All the files are stored inside a bucket named ``bucket`` on ``host`` which Depot
    connects to using ``access_key_id`` and ``secret_access_key``.
 
    Additional options include:
        * ``host`` which can be used to specify an host different from Amazon
          AWS S3 Storage
        * ``policy`` which can be used to specify a canned ACL policy of either 
          ``private`` or ``public-read``.
        * ``encrypt_key`` which can be specified to use the server side
          encryption feature.
        * ``prefix`` parameter can be used to store all files under
          specified prefix. Use a prefix like **dirname/** (*see trailing slash*)
          to store in a subdirectory.
    """

    def __init__(self, access_key_id, secret_access_key, bucket=None, host=None,
                 policy=None, encrypt_key=False, prefix=''):
        policy = policy or CANNED_ACL_PUBLIC_READ
        assert policy in [CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE], (
            "Key policy must be %s or %s" % (CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE))
        self._policy = policy or CANNED_ACL_PUBLIC_READ
        self._encrypt_key = encrypt_key

        if bucket is None:
            bucket = 'filedepot-%s' % (access_key_id.lower(),)

        kw = {}
        if host is not None:
            kw['host'] = host
        self._conn = S3Connection(access_key_id, secret_access_key, **kw)
        bucket = self._conn.lookup(bucket) or self._conn.create_bucket(bucket)
        self._bucket_driver = BucketDriver(bucket, prefix)


    def get(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        key = self._bucket_driver.get_key(fileid)
        if key is None:
            raise IOError('File %s not existing' % fileid)

        return S3StoredFile(fileid, key)

    def __save_file(self, key, content, filename, content_type=None):
        if filename:
            filename = percent_encode(filename, safe='!#$&+-.^_`|~', encoding='utf-8')
        key.set_metadata('content-type', content_type)
        key.set_metadata(
            'x-depot-filename',
            filename
        )
        key.set_metadata('x-depot-modified', utils.timestamp())
        key.set_metadata(
            'Content-Disposition',
            make_content_disposition('inline', filename))

        if hasattr(content, 'read'):
            can_seek_and_tell = True
            try:
                pos = content.tell()
                content.seek(pos)
            except:
                can_seek_and_tell = False

            if can_seek_and_tell:
                key.set_contents_from_file(content, policy=self._policy,
                                           encrypt_key=self._encrypt_key)
            else:
                key.set_contents_from_string(content.read(), policy=self._policy,
                                             encrypt_key=self._encrypt_key)
        else:
            if isinstance(content, unicode_text):
                raise TypeError('Only bytes can be stored, not unicode')
            key.set_contents_from_string(content, policy=self._policy,
                                         encrypt_key=self._encrypt_key)

    def create(self, content, filename=None, content_type=None):
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        new_file_id = str(uuid.uuid1())
        key = self._bucket_driver.new_key(new_file_id)
        self.__save_file(key, content, filename, content_type)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        content, filename, content_type = self.fileinfo(content, filename, content_type,
                                                        lambda: self.get(fileid))

        key = self._bucket_driver.get_key(fileid)
        self.__save_file(key, content, filename, content_type)
        return fileid

    def delete(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        k = self._bucket_driver.get_key(fileid)
        if k:
            k.delete()

    def exists(self, file_or_id):
        fileid = self.fileid(file_or_id)
        _check_file_id(fileid)

        k = self._bucket_driver.get_key(fileid)
        return k is not None

    def list(self):
        return self._bucket_driver.list_key_names()


def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        uuid.UUID('{%s}' % file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)
