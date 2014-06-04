from nose.tools import raises
from depot.io.local import LocalFileStorage
from depot.io.gridfs import GridFSStorage
import shutil
import mock
import datetime
from io import BytesIO
from tempfile import TemporaryFile
from pymongo import MongoClient
import gridfs


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
                  temp):
            fid = self.fs.create(d, 'filename')
            f = self.fs.get(fid)
            assert f.read() == FILE_CONTENT

    def test_content_type(self):
        for fname, ctype in (('filename', 'application/octet-stream'),
                             ('image.png', 'image/png'),
                             ('file.txt', 'text/plain')):
            file_id = self.fs.create(FILE_CONTENT, fname)
            f = self.fs.get(file_id)
            assert f.content_type == ctype, (fname, ctype)

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

    @raises(TypeError)
    def test_storing_unicode_is_prevented(self):
        file_id = self.fs.create(FILE_CONTENT.decode('utf-8'), 'file.txt')


class TestLocalFileStorage(BaseStorageTestFixture):
    def setup(self):
        self.fs = LocalFileStorage('./lfs')

    def teardown(self):
        try:
            shutil.rmtree('./lfs')
        except:
            pass


class TestGridFSFileStorage(BaseStorageTestFixture):
    def setup(self):
        self.db = MongoClient().gridfs_example
        fs = gridfs.GridFS(self.db, collection='testfs')
        self.fs = GridFSStorage(fs)

    def teardown(self):
        self.db.drop_collection('testfs')
