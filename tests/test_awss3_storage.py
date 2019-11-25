import os
import uuid
import time
import mock
import requests
from flaky import flaky

from nose import SkipTest

from depot._compat import PY2, unicode_text


S3Storage = None
FILE_CONTENT = b'HELLO WORLD'


@flaky
class TestS3FileStorage(object):
    @classmethod
    def setupClass(cls):
        # Travis runs multiple tests concurrently on fake machines that might
        # collide on pid and hostid, so use an uuid1 which should be fairly random
        # thanks to clock_seq
        cls.run_id = '%s-%s' % (uuid.uuid1().hex, os.getpid())

        try:
            global S3Storage
            from depot.io.awss3 import S3Storage
        except ImportError:
            raise SkipTest('Boto not installed')

        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            raise SkipTest('Amazon S3 credentials not available')

        cls.default_bucket_name = 'filedepot-%s' % (access_key_id.lower(), )
        cls.cred = (access_key_id, secret_access_key)

        bucket_name = 'filedepot-testfs-%s' % cls.run_id
        cls.fs = S3Storage(access_key_id, secret_access_key, bucket_name)
        while not cls.fs._conn.lookup(bucket_name):
            # Wait for bucket to exist, to avoid flaky tests...
            time.sleep(0.5)

    @classmethod
    def teardownClass(cls):
        if not cls.fs._conn.lookup(cls.fs._bucket_driver.bucket.name):
            return
        
        keys = [key.name for key in cls.fs._bucket_driver.bucket]
        if keys:
            cls.fs._bucket_driver.bucket.delete_keys(keys)

        try:
            cls.fs._conn.delete_bucket(cls.fs._bucket_driver.bucket.name)
            while cls.fs._conn.lookup(cls.fs._bucket_driver.bucket.name):
                # Wait for bucket to be deleted, to avoid flaky tests...
                time.sleep(0.5)
        except:
            pass

    def test_fileoutside_depot(self):
        fid = str(uuid.uuid1())
        key = self.fs._bucket_driver.new_key(fid)
        key.set_contents_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.read() == FILE_CONTENT

    def test_invalid_modified(self):
        fid = str(uuid.uuid1())
        key = self.fs._bucket_driver.new_key(fid)
        key.set_metadata('x-depot-modified', 'INVALID')
        key.set_contents_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.last_modified is None, f.last_modified

    def test_creates_bucket_when_missing(self):
        with mock.patch('boto.s3.connection.S3Connection.lookup', return_value=None):
            with mock.patch('boto.s3.connection.S3Connection.lookup',
                            return_value='YES') as mock_create:
                fs = S3Storage(*self.cred)
                mock_create.assert_called_with(self.default_bucket_name)

    def test_default_bucket_name(self):
        with mock.patch('boto.s3.connection.S3Connection.lookup', return_value='YES'):
            fs = S3Storage(*self.cred)
            assert fs._bucket_driver.bucket == 'YES'

    def test_public_url(self):
        fid = str(uuid.uuid1())
        key = self.fs._bucket_driver.new_key(fid)
        key.set_contents_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert '.s3.amazonaws.com' in f.public_url, f.public_url
        assert f.public_url.endswith('/%s' % fid), f.public_url

    def test_content_disposition(self):
        file_id = self.fs.create(b'content', unicode_text('test.txt'), 'text/plain')
        test_file = self.fs.get(file_id)
        response = requests.get(test_file.public_url)
        assert response.headers['Content-Disposition'] == "inline;filename=\"test.txt\";filename*=utf-8''test.txt"
