import uuid
from nose.tools import raises
from nose import SkipTest
import shutil
import mock
import datetime
from io import BytesIO
from tempfile import TemporaryFile, NamedTemporaryFile
import os
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

    @raises(IOError)
    def test_notexisting(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)
        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

        self.fs.get(file_id)

    @raises(ValueError)
    def test_invalidid(self):
        f = self.fs.get('NOTANID')

    def test_creation_inputs(self):
        temp = TemporaryFile()
        temp.write(FILE_CONTENT)
        temp.seek(0)

        for d in (FILE_CONTENT,
                  BytesIO(FILE_CONTENT),
                  temp,
                  create_cgifs('text/plain', FILE_CONTENT, 'file.txt')):
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

    def test_filewithname(self):
        temp = NamedTemporaryFile()
        temp.write(FILE_CONTENT)
        temp.seek(0)

        file_id = self.fs.create(temp)

        f = self.fs.get(file_id)
        assert f.content_type == 'application/octet-stream'
        assert temp.name.endswith(f.filename)
        assert f.read() == FILE_CONTENT

    def test_another_storage(self):
        file_id = self.fs.create(FILE_CONTENT, filename='file.txt', content_type='text/plain')
        f = self.fs.get(file_id)

        file2_id = self.fs.create(f)
        assert file2_id != f.file_id

        f2 = self.fs.get(file_id)
        assert f2.filename == f.filename
        assert f2.content_type == f.content_type
        assert f2.filename == 'file.txt'
        assert f2.content_type == 'text/plain'

    def test_repr(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        assert repr(f).endswith('%s filename=file.txt '
                                'content_type=text/plain '
                                'last_modified=%s>' % (f.file_id, f.last_modified))

    @raises(IOError)
    def test_replace_only_existing(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert self.fs.exists(file_id)
        self.fs.delete(file_id)
        assert not self.fs.exists(file_id)

        self.fs.replace(file_id, FILE_CONTENT)

    @raises(ValueError)
    def test_replace_invalidid(self):
        self.fs.replace('INVALIDID', FILE_CONTENT)

    def test_replace_keeps_filename(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        self.fs.replace(f, b'NEW CONTENT')
        f2 = self.fs.get(f.file_id)

        assert f2.file_id == f.file_id
        assert f.filename == f2.filename, (f.filename, f2.filename)
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

    @raises(ValueError)
    def test_exists_invalidid(self):
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

    @raises(ValueError)
    def test_delete_invalidid(self):
        self.fs.delete('INVALIDID')

    def test_stored_files_are_only_readable(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        assert f.readable()
        assert not f.writable()
        assert not f.seekable()

    @raises(TypeError)
    def test_storing_unicode_is_prevented(self):
        file_id = self.fs.create(FILE_CONTENT.decode('utf-8'), 'file.txt')

    @raises(TypeError)
    def test_replacing_unicode_is_prevented(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        self.fs.replace(f, FILE_CONTENT.decode('utf-8'))

    def test_closing_file(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        assert f.closed is False
        with f:
            f.read()
        assert f.closed is True

    @raises(ValueError)
    def test_reading_from_closed_file_is_prevented(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        f.close()

        f.read()

    def test_name_is_an_alias_for_filename(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)
        assert f.name == f.filename


class TestLocalFileStorage(BaseStorageTestFixture):
    def setup(self):
        from depot.io.local import LocalFileStorage
        self.fs = LocalFileStorage('./lfs')

    def teardown(self):
        shutil.rmtree('./lfs', ignore_errors=True)


class TestGridFSFileStorage(BaseStorageTestFixture):
    def setup(self):
        try:
            from depot.io.gridfs import GridFSStorage
        except ImportError:
            raise SkipTest('PyMongo not installed')

        self.fs = GridFSStorage('mongodb://localhost/gridfs_example', 'testfs')

    def teardown(self):
        self.fs._db.drop_collection('testfs')


class TestS3FileStorage(BaseStorageTestFixture):
    @classmethod
    def setup_class(cls):
        try:
            from depot.io.awss3 import S3Storage
        except ImportError:
            raise SkipTest('Boto not installed')

        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            raise SkipTest('Amazon S3 credentials not available')

        PID = os.getpid()
        NODE = str(uuid.uuid1()).rsplit('-', 1)[-1]
        BUCKET_NAME = 'fdtest-%s-%s-%s' % (access_key_id.lower(), NODE, PID)
        cls.fs = S3Storage(access_key_id, secret_access_key, BUCKET_NAME)

    def teardown(self):
        keys = [key.name for key in self.fs._bucket]
        if keys:
            self.fs._bucket.delete_keys(keys)

    @classmethod
    def teardown_class(cls):
        try:
            cls.fs._conn.delete_bucket(cls.fs._bucket.name)
        except:
            pass
