"""
Provides FileStorage implementation for Amazon S3 through boto3 library.

This is useful for storing files in S3.

"""
from __future__ import absolute_import

from datetime import datetime
import uuid
import boto3
from botocore.exceptions import ClientError
from depot._compat import unicode_text, percent_encode, percent_decode
from depot.utils import make_content_disposition

from .interfaces import FileStorage, StoredFile
from . import utils

CANNED_ACL_PUBLIC_READ = 'public-read'
CANNED_ACL_PRIVATE = 'private'


class S3StoredFile(StoredFile):
    def __init__(self, file_id, key):
        _check_file_id(file_id)
        self._closed = False
        self._key = key
        self._body = None
        filename = key.metadata.get('x-depot-filename')
        if filename:
            filename = percent_decode(filename)

        metadata_info = {'filename': filename,
                         'content_type': key.content_type,
                         'content_length': key.content_length,
                         'last_modified': None}

        try:
            last_modified = key.metadata.get('x-depot-modified')
            if last_modified:
                metadata_info['last_modified'] = datetime.strptime(last_modified,
                                                                   '%Y-%m-%d %H:%M:%S')
        except:
            pass

        super(S3StoredFile, self).__init__(file_id=file_id, **metadata_info)

    def read(self, n=-1):
        if self.closed:
            raise ValueError("cannot read from a closed file")

        if self._body is None:
            self._body = self._key.get()['Body']

        if n <= 0:
            n = None
        return self._body.read(n)

    def close(self):
        self._closed = True
        if self._body is not None:
            self._body.close()

    @property
    def closed(self):
        return self._closed

    @property
    def public_url(self):
        expires_in = 31536000 # 1 YEAR
        url = self._key.meta.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._key.Bucket().name, 'Key': self._key.key},
            ExpiresIn=expires_in
        )
        # Remove query auth
        url = url.split('?', 1)[0]
        return url


class BucketDriver(object):

    def __init__(self, s3, bucket, prefix):
        self.s3 = s3
        self.bucket = bucket
        self.prefix = prefix

    def get_key(self, key_name):
        k = self.bucket.Object('%s%s' % (self.prefix, key_name))
        try:
            k.reload()
        except ClientError as exc:
            k = None
            if exc.response['Error']['Code'] != '404':
                raise
        return k

    def new_key(self, key_name):
        return self.bucket.Object('%s%s' % (self.prefix, key_name))

    def list_key_names(self):
        keys = self.bucket.objects.filter(Prefix=self.prefix)
        return [k.key[len(self.prefix):] for k in keys]


class S3Storage(FileStorage):
    """:class:`depot.io.interfaces.FileStorage` implementation that stores files on S3.

    **This is a version implemented on top of boto3**.
    Installing ``boto3`` as a dependency is required to use this.

    All the files are stored inside a bucket named ``bucket`` on ``host`` which Depot
    connects to using ``access_key_id`` and ``secret_access_key``.
 
    Additional options include:
        * ``region`` which can be used to specify the AWS region.
        * ``endpoint_url`` which can be used to specify an host different from Amazon
          AWS S3 Storage
        * ``policy`` which can be used to specify a canned ACL policy of either
          ``private`` or ``public-read``.
        * ``storage_class`` which can be used to specify a class of storage.
        * ``prefix`` parameter can be used to store all files under 
          specified prefix. Use a prefix like **dirname/** (*see trailing slash*)
          to store in a subdirectory.
    """

    def __init__(self, access_key_id, secret_access_key, bucket=None, region_name=None,
                 policy=None, storage_class=None, endpoint_url=None, prefix=''):
        policy = policy or CANNED_ACL_PUBLIC_READ
        assert policy in [CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE], (
            "Key policy must be %s or %s" % (CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE))
        self._policy = policy or CANNED_ACL_PUBLIC_READ
        self._storage_class = storage_class or 'STANDARD'

        if bucket is None:
            bucket = 'filedepot-%s' % (access_key_id.lower(),)

        kw = {}
        if endpoint_url is not None:
            kw['endpoint_url'] = endpoint_url
        if region_name is not None:
            kw['region_name'] = region_name
        self._conn = boto3.Session(aws_access_key_id=access_key_id,
                                   aws_secret_access_key=secret_access_key)
        self._s3 = self._conn.resource('s3', **kw)
        bucket = self._s3.Bucket(bucket)

        # Create bucket if it doesn't exist.
        buckets = set(b['Name'] for b in self._s3.meta.client.list_buckets()['Buckets'])
        if bucket.name not in buckets:
            bucket.create()
            bucket.wait_until_exists()

        self._bucket_driver = BucketDriver(self._s3, bucket, prefix)

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
        attrs = {
            'ACL': self._policy,
            'StorageClass': self._storage_class,
            'Metadata': {
                'x-depot-filename': filename,
                'x-depot-modified': utils.timestamp()
            },
            'ContentType': content_type,
            'ContentDisposition': make_content_disposition('inline', filename)
        }

        if hasattr(content, 'read'):
            try:
                pos = content.tell()
                content.seek(pos)
            except:
                content = content.read()
            key.put(Body=content, **attrs)
        else:
            if isinstance(content, unicode_text):
                raise TypeError('Only bytes can be stored, not unicode')
            key.put(Body=content, **attrs)

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
