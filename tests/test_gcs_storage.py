import io
import os
import uuid
import json
import requests
from flaky import flaky
import unittest
from unittest import SkipTest
from google.cloud.exceptions import NotFound

from depot._compat import PY2, unicode_text
from depot.io.gcs import GCSStorage

FILE_CONTENT = b'HELLO WORLD'


@flaky
class TestGCSStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_id = '%s-%s' % (uuid.uuid1().hex, os.getpid())
        cls._prefix = ''

        try:
            global GCSStorage
            from depot.io.gcs import GCSStorage
        except ImportError:
            raise SkipTest('Google Cloud Storage not installed')
        
        cls._bucket = 'filedepot-testfs-%s' % cls.run_id
        env = os.environ
        google_credentials = env.get('GOOGLE_SERVICE_CREDENTIALS')
        if not google_credentials:
            raise SkipTest('GOOGLE_SERVICE_CREDENTIALS environment variable not set')
        google_credentials = json.loads(google_credentials)
        cls.fs = GCSStorage(project_id=google_credentials["project_id"], 
                            credentials=google_credentials, 
                            bucket=cls._bucket, 
                            prefix=cls._prefix)

    @classmethod
    def tearDownClass(cls):
        for blob in cls.fs.bucket.list_blobs():
            blob.delete()
        
        try:
            cls.fs.bucket.delete()
        except NotFound:
            pass

    def test_fileoutside_depot(self):
        fid = str(uuid.uuid1())
        blob = self.fs.bucket.blob(self._prefix+fid)
        blob.upload_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.read() == FILE_CONTENT

    def test_public_url(self):
        fid = str(uuid.uuid1())
        blob = self.fs.bucket.blob(self._prefix+fid)
        blob.upload_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.public_url.endswith('/%s' % self._prefix+fid), f.public_url

    def test_content_disposition(self):
        file_id = self.fs.create(io.BytesIO(b'content'), unicode_text('test.txt'), 'text/plain')
        test_file = self.fs.get(file_id)
        response = requests.get(test_file.public_url)
        assert response.headers['Content-Disposition'] == "inline;filename=\"test.txt\";filename*=utf-8''test.txt"

    def test_storage_non_ascii_filenames(self):
        filename = u'ملف.pdf'
        new_file_id = self.fs.create(
            io.BytesIO(FILE_CONTENT),
            filename=filename,
            content_type='application/pdf'
        )

        assert new_file_id is not None
    
