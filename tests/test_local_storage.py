from filedepot.io.local import LocalFileStorage
import shutil
import os
import mock
import datetime


FILE_CONTENT = b'HELLO WORLD'


class TestLocalFileStorage(object):
    def setup(self):
        self.fs = LocalFileStorage('./lfs')

    def teardown(self):
        try:
            shutil.rmtree('./lfs')
        except:
            pass

    def test_bytes_creation(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert FILE_CONTENT == open(os.path.join('./lfs', file_id, 'file')).read()

    def test_creation_readback(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')

        f = self.fs.get(file_id)
        assert f.read() == FILE_CONTENT

    def test_creation_metadata(self):
        with mock.patch('filedepot.io.local._file_timestamp', return_value='2001-01-01 00:00:01'):
            file_id = self.fs.create(FILE_CONTENT, 'file.txt')

        f = self.fs.get(file_id)
        assert f.filename == 'file.txt', f.filename
        assert f.last_modified == datetime.datetime(2001, 1, 1, 0, 0, 1), f.last_modified
        assert f.content_type == 'text/plain', f.content_type
