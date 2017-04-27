from nose import SkipTest
from depot.io.gridfs import GridFSStorage

FILE_CONTENT = b'HELLO WORLD'


class TestGridFSFileStorage(object):
    def setup(self):
        try:
            import pymongo.errors
            self.fs = GridFSStorage('mongodb://localhost/gridfs_example', 'testfs')
        except pymongo.errors.ConnectionFailure:
            raise SkipTest('MongoDB not running')

    def teardown(self):
        self.fs._db.drop_collection('testfs')

    def test_fileoutside_depot(self):
        fileid = self.fs._gridfs.put(FILE_CONTENT)

        f = self.fs.get(str(fileid))
        assert f.read() == FILE_CONTENT
