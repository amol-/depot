from depot.io.gridfs import GridFSStorage
from pymongo import MongoClient
import gridfs


FILE_CONTENT = b'HELLO WORLD'


class TestGridFSFileStorage(object):
    def setup(self):
        self.db = MongoClient().gridfs_example
        self.gridfs = gridfs.GridFS(self.db, collection='testfs')
        self.fs = GridFSStorage(self.gridfs)

    def teardown(self):
        self.db.drop_collection('testfs')

    def test_fileoutside_depot(self):
        fileid = self.gridfs.put(FILE_CONTENT)

        f = self.fs.get(str(fileid))
        assert f.read() == FILE_CONTENT