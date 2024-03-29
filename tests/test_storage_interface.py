# -*- coding: utf-8 -*-
import uuid
import unittest
import json
from flaky import flaky
import shutil
import mock
import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile
import os
from depot.io.utils import FileIntent
from tests.utils import create_cgifs

FILE_CONTENT = b'HELLO WORLD'


class BaseStorageTestFixture(object):
    def test_creation_readback(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        assert f.read() == FILE_CONTENT

    def test_creation_metadata(self):
        with mock.patch('depot.io.utils.timestamp', return_value='2001-01-01 00:00:01'):
            file_id = self.fs.create(FILE_CONTENT, 'file.txt')

        f = self.fs.get(file_id)
        assert f.filename == 'file.txt', f.filename
        assert f.last_modified == datetime.datetime(2001, 1, 1, 0, 0, 1), f.last_modified
        assert f.content_type == 'text/plain', f.content_type

    def test_notexisting(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)
        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

        with self.assertRaises(IOError):
            self.fs.get(file_id)

    def test_invalidid(self):
        with self.assertRaises(ValueError):
            f = self.fs.get('NOTANID')

    def test_creation_inputs(self):
        temp = NamedTemporaryFile()
        temp.write(FILE_CONTENT)
        temp.seek(0)

        for d in (FILE_CONTENT,
                  BytesIO(FILE_CONTENT),
                  temp,
                  create_cgifs('text/plain', FILE_CONTENT, 'file.txt'),
                  FileIntent(FILE_CONTENT, 'file.txt', 'text/plain')):
            fid = self.fs.create(d, 'filename')
            f = self.fs.get(fid)
            assert f.read() == FILE_CONTENT

    def test_content_type_by_name(self):
        for fname, ctype in (('filename', 'application/octet-stream'),
                             ('image.png', 'image/png'),
                             ('file.txt', 'text/plain')):
            file_id = self.fs.create(FILE_CONTENT, fname)
            f = self.fs.get(file_id)
            assert f.content_type == ctype, (fname, ctype)

    def test_cgifieldstorage(self):
        cgifs = create_cgifs('text/plain', FILE_CONTENT, 'file.txt')
        file_id = self.fs.create(cgifs)

        f = self.fs.get(file_id)
        assert f.content_type == 'text/plain'
        assert f.filename == 'file.txt'
        assert f.read() == FILE_CONTENT

    def test_fileintent(self):
        file_id = self.fs.create(FileIntent(FILE_CONTENT, 'file.txt', 'text/plain'))

        f = self.fs.get(file_id)
        assert f.content_type == 'text/plain', f.content_type
        assert f.filename == 'file.txt', f.filename
        assert f.read() == FILE_CONTENT

    def test_filewithname(self):
        temp = NamedTemporaryFile()
        temp.write(FILE_CONTENT)
        temp.seek(0)

        file_id = self.fs.create(temp)

        f = self.fs.get(file_id)
        assert f.content_type == 'application/octet-stream'
        assert temp.name.endswith(f.filename)
        assert f.read() == FILE_CONTENT

    def test_filewithnonasciiname(self):
        filename = u'些公.pdf'
        temp = NamedTemporaryFile()
        temp.write(FILE_CONTENT)
        temp.seek(0)

        file_id = self.fs.create(
            temp,
            filename=filename,
            content_type='application/pdf'
        )

        f = self.fs.get(file_id)
        assert f.content_type == 'application/pdf'
        assert f.read() == FILE_CONTENT

    def test_another_copy(self):
        file_id = self.fs.create(FILE_CONTENT, filename='file.txt', content_type='text/plain')
        f = self.fs.get(file_id)

        file2_id = self.fs.create(f)
        assert file2_id != f.file_id

        f2 = self.fs.get(file2_id)
        assert f2.filename == f.filename
        assert f2.content_type == f.content_type
        assert f2.filename == 'file.txt', (f.filename, f2.filename)
        assert f2.content_type == 'text/plain'

    def test_copy_to_other_storage(self):
        file_id = self.fs.create(FILE_CONTENT, filename='file.txt', content_type='text/plain')
        f = self.fs.get(file_id)

        other_storage = self.get_storage("otherbucket-%s" % uuid.uuid1().hex)
        try:
            other_storage.replace(f, f)

            assert other_storage.exists(f.file_id)
            assert other_storage.get(f.file_id).read() == FILE_CONTENT
            assert other_storage.get(f.file_id).filename == f.filename
        finally:
            self.delete_storage(other_storage)

    def test_backup(self):
        file_ids = set()
        for i in range(10):
            file_ids.add(
                self.fs.create(FILE_CONTENT, filename='file-%s.txt' %i,
                               content_type='text/plain')
            )

        other_storage = self.get_storage("otherbucket-%s" % uuid.uuid1().hex)
        existing_files = self.fs.list()
        try:
            for f_id in existing_files:
                f = self.fs.get(f_id)
                other_storage.replace(f, f)

            assert set(other_storage.list()) == file_ids
        finally:
            self.delete_storage(other_storage)


    def test_repr(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        assert repr(f).endswith('%s filename=file.txt '
                                'content_type=text/plain '
                                'last_modified=%s>' % (f.file_id, f.last_modified))

    def test_replace_only_existing(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)
        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

        with self.assertRaises(IOError):
            self.fs.replace(file_id, FILE_CONTENT)

    def test_replace_invalidid(self):
        with self.assertRaises(ValueError):
            self.fs.replace('INVALIDID', FILE_CONTENT)

    def test_replace_keeps_filename(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        self.fs.replace(f, b'NEW CONTENT')
        f2 = self.fs.get(f.file_id)

        assert f2.file_id == f.file_id
        assert f.filename == f2.filename
        assert f.read() == b'NEW CONTENT'
        assert f2.content_type == 'text/plain'

    def test_replace_updates_data(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        self.fs.replace(f, b'NEW CONTENT', 'file.png')
        f2 = self.fs.get(f.file_id)

        assert f2.file_id == f.file_id
        assert f2.filename == 'file.png'
        assert f2.read() == b'NEW CONTENT'
        assert f2.content_type == 'image/png'

    def test_exists(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)

        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

    def test_list(self):
        file_ids = list()
        for i in range(3):
            file_ids.append(self.fs.create(FILE_CONTENT, 'file_for_listing-{0}.txt'.format(i)))

        existing_files = self.fs.list()
        for _id in file_ids:
            assert _id in existing_files, ("{0} not in {1}".format(_id, file_ids))

    def test_exists_invalidid(self):
        with self.assertRaises(ValueError):
            self.fs.exists('INVALIDID')

    def test_delete(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)

        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

    def test_delete_idempotent(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)

        self.fs.delete(file_id)
        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

    def test_delete_invalidid(self):
        with self.assertRaises(ValueError):
            self.fs.delete('INVALIDID')

    def test_stored_files_are_only_readable(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        assert f.readable()
        assert not f.writable()
        assert not f.seekable()

    def test_storing_unicode_is_prevented(self):
        with self.assertRaises(TypeError):
            file_id = self.fs.create(FILE_CONTENT.decode('utf-8'), 'file.txt')

    def test_replacing_unicode_is_prevented(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        with self.assertRaises(TypeError):
            self.fs.replace(f, FILE_CONTENT.decode('utf-8'))

    def test_closing_file(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        assert f.closed is False
        with f:
            f.read()
        assert f.closed is True

    def test_reading_from_closed_file_is_prevented(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        f.close()

        with self.assertRaises(ValueError):
            f.read()

    def test_name_is_an_alias_for_filename(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        assert f.name == f.filename

    def test_create_from_bytes_with_default_filename(self):
        file_id = self.fs.create(b'this is the content')
        f = self.fs.get(file_id)
        assert f.name == 'unnamed'


class TestLocalFileStorage(unittest.TestCase, BaseStorageTestFixture):
    @classmethod
    def get_storage(cls, bucket_name):
        from depot.io.local import LocalFileStorage
        return LocalFileStorage('./lfs/%s' % bucket_name)

    @classmethod
    def delete_storage(cls, storage):
        shutil.rmtree(storage.storage_path, ignore_errors=True)

    def setUp(self):
        self.fs = self.get_storage("default_bucket")

    def tearDown(self):
        self.delete_storage(self.fs)


class TestGridFSFileStorage(unittest.TestCase, BaseStorageTestFixture):
    @classmethod
    def get_storage(cls, collection_name):
        from depot.io.gridfs import GridFSStorage
        import pymongo.errors
        try:
            fs = GridFSStorage('mongodb://localhost/gridfs_example?serverSelectionTimeoutMS=100', collection_name)
            fs._gridfs.exists("")  # Any operation to test that mongodb is up.
            return fs
        except pymongo.errors.ConnectionFailure:
            return None

    @classmethod
    def delete_storage(cls, storage):
        storage._db.drop_collection('%s.files' % storage._collection)
        storage._db.drop_collection('%s.chunks' % storage._collection)

    @classmethod
    def setUpClass(cls):
        try:
            from depot.io.gridfs import GridFSStorage
        except ImportError:
            cls.skipTest('PyMongo not installed')

        cls.fs = cls.get_storage('testfs')

    def setUp(self):
        if self.fs is None:
            self.skipTest('MongoDB not running')

    def tearDown(self):
        self.delete_storage(self.fs)


@flaky
class TestS3FileStorage(unittest.TestCase, BaseStorageTestFixture):

    @classmethod
    def get_storage(cls, bucket_name):
        from depot.io.awss3 import S3Storage

        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            return None
        
        return S3Storage(access_key_id, secret_access_key, bucket_name)

    @classmethod
    def delete_storage(cls, storage):
        keys = [key.name for key in storage._bucket_driver.bucket]
        if keys:
            storage._bucket_driver.bucket.delete_keys(keys)

        try:
            storage._conn.delete_bucket(storage._bucket_driver.bucket.name)
        except:
            pass

    @classmethod
    def setUpClass(cls):
        try:
            from depot.io.awss3 import S3Storage
        except ImportError:
            raise unittest.SkipTest('Boto not installed')

        BUCKET_NAME = 'fdtest-%s-%s' % (uuid.uuid1(), os.getpid())
        cls.fs = cls.get_storage(BUCKET_NAME)
        if cls.fs is None:
            raise unittest.SkipTest('Amazon S3 credentials not available')

    def tearDown(self):
        keys = [key.name for key in self.fs._bucket_driver.bucket]
        if keys:
            self.fs._bucket_driver.bucket.delete_keys(keys)

    @classmethod
    def tearDownClass(cls):
        cls.delete_storage(cls.fs)


@flaky
class TestS3FileStorageWithPrefix(TestS3FileStorage):

    @classmethod
    def get_storage(cls, bucket_name):
        from depot.io.awss3 import S3Storage

        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            return None

        return S3Storage(
            access_key_id,
            secret_access_key,
            bucket_name,
            prefix='my-prefix/')


class TestMemoryFileStorage(unittest.TestCase, BaseStorageTestFixture):
    @classmethod
    def get_storage(cls, _):
        from depot.io.memory import MemoryFileStorage
        return MemoryFileStorage()

    @classmethod
    def delete_storage(cls, storage):
        map(storage.delete, storage.list())

    def setUp(self):
        self.fs = self.get_storage(None)

    def tearDown(self):
        self.delete_storage(self.fs)


@flaky
class TestBoto3FileStorage(unittest.TestCase, BaseStorageTestFixture):

    @classmethod
    def get_storage(cls, bucket_name):
        from depot.io.boto3 import S3Storage

        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            return None

        return S3Storage(access_key_id, secret_access_key, bucket_name)

    @classmethod
    def delete_storage(cls, storage):
        for obj in storage._bucket_driver.bucket.objects.all():
            obj.delete()
        try:
            storage._bucket_driver.bucket.delete()
        except:
            pass

    @classmethod
    def setUpClass(cls):
        try:
            from depot.io.boto3 import S3Storage
        except ImportError:
            raise unittest.SkipTest('Boto3 not installed')

        BUCKET_NAME = 'fdtest-%s-%s' % (uuid.uuid1(), os.getpid())
        cls.fs = cls.get_storage(BUCKET_NAME)
        if not cls.fs:
            raise unittest.SkipTest('Amazon S3 credentials not available')

    def tearDown(self):
        for obj in self.fs._bucket_driver.bucket.objects.all():
            obj.delete()

    @classmethod
    def tearDownClass(cls):
        cls.delete_storage(cls.fs)


@flaky
class TestGCSFileStorage(unittest.TestCase, BaseStorageTestFixture):

    @classmethod
    def get_storage(cls, bucket_name):
        from depot.io.gcs import GCSStorage

        env = os.environ
        google_credentials = env.get('GOOGLE_SERVICE_CREDENTIALS')
        if not google_credentials:
            return None
        google_credentials = json.loads(google_credentials)

        return GCSStorage(project_id=google_credentials['project_id'],
                          credentials=google_credentials, 
                          bucket=bucket_name)

    @classmethod
    def delete_storage(cls, storage):
        for blob in storage.bucket.list_blobs():
            blob.delete()
        try:
            storage.bucket.delete()
        except:
            pass

    @classmethod
    def setUpClass(cls):
        try:
            from depot.io.gcs import GCSStorage
        except ImportError:
            raise unittest.SkipTest('Google Cloud Storage not installed')

        BUCKET_NAME = 'fdtest-%s-%s' % (uuid.uuid1(), os.getpid())
        cls.fs = cls.get_storage(bucket_name=BUCKET_NAME)
        if cls.fs is None:
            raise unittest.SkipTest('GOOGLE_SERVICE_CREDENTIALS environment variable not set')

    def tearDown(self):
        for blob in self.fs.bucket.list_blobs():
            blob.delete()

    @classmethod
    def tearDownClass(cls):
        cls.delete_storage(cls.fs)