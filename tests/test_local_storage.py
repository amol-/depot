import shutil
import os
import unittest
from depot.io.local import LocalFileStorage

FILE_CONTENT = b'HELLO WORLD'


class TestLocalFileStorage(unittest.TestCase):
    def setUp(self):
        self.fs = LocalFileStorage('./lfs')

    def tearDown(self):
        shutil.rmtree('./lfs', ignore_errors=True)

    def test_creation(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        assert FILE_CONTENT == open(os.path.join('./lfs', file_id, 'file'), 'rb').read()

    def test_corrupted_metadata(self):
        file_id = self.fs.create(FILE_CONTENT, 'file.txt')
        f = self.fs.get(file_id)

        with open(f._metadata_path, 'w') as mdf:
            mdf.write('NOT JSON')

        did_detect_corrupted_metadata = False
        try:
            f = self.fs.get(file_id)
        except ValueError:
            did_detect_corrupted_metadata = True

        assert did_detect_corrupted_metadata

