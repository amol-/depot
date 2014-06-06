from depot.io.gridfs import GridFSStorage

FILE_CONTENT = b'HELLO WORLD'


class TestGridFSFileStorage(object):
    def setup(self):
        self.fs = GridFSStorage('mongodb://localhost/gridfs_example', 'testfs')

    def teardown(self):
        self.fs._db.drop_collection('testfs')

    def test_fileoutside_depot(self):
        fileid = self.fs._gridfs.put(FILE_CONTENT)

        f = self.fs.get(str(fileid))
        assert f.read() == FILE_CONTENT