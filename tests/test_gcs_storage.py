import io
import os
import uuid
import requests
from flaky import flaky
from unittest import SkipTest
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account

from depot._compat import PY2, unicode_text
from depot.io.gcs import GCSStorage

FILE_CONTENT = b'HELLO WORLD'


@flaky
class TestGCSStorage(object):
    @classmethod
    def setUpClass(cls):
        cls.run_id = '%s-%s' % (uuid.uuid1().hex, os.getpid())

        try:
            global GCSStorage
            from depot.io.gcs import GCSStorage
        except ImportError:
            raise SkipTest('Google Cloud Storage not installed')
        
        cls._bucket = 'filedepot-testfs-%s' % cls.run_id
        env = os.environ
        if os.getenv("STORAGE_EMULATOR_HOST"):
            cls.fs = GCSStorage(bucket=cls._bucket)
        else:
            if not env.get('GOOGLE_APPLICATION_CREDENTIALS'):
                raise SkipTest('GOOGLE_APPLICATION_CREDENTIALS environment variable not set')
            cls._gcs_credentials  = service_account.Credentials.from_service_account_file(env.get('GOOGLE_APPLICATION_CREDENTIALS'))
            cls._project_id = cls._gcs_credentials .project_id
            cls.fs = GCSStorage(project_id=cls._project_id,credentials=cls._gcs_credentials , bucket=cls._bucket)

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
        blob = self.fs.bucket.blob(fid)
        blob.upload_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.read() == FILE_CONTENT


    def test_get_key_failure(self):
        non_existent_key = str(uuid.uuid1())
        try:
            self.fs.get(non_existent_key)
        except NotFound:
            pass
        else:
            assert False, 'Should have raised NotFound'

    def test_public_url(self):
        fid = str(uuid.uuid1())
        blob = self.fs.bucket.blob(fid)
        blob.upload_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.public_url.endswith('/%s' % fid), f.public_url

    def test_content_disposition(self):
        file_id = self.fs.create(io.BytesIO(b'content'), unicode_text('test.txt'), 'text/plain')
        test_file = self.fs.get(file_id)
        response = requests.get(test_file.public_url)
        assert response.headers['Content-Disposition'] == "inline;filename=\"test.txt\";filename*=utf-8''test.txt"


    def test_storage_non_ascii_filenames(self):
        filename = u'ملف.pdf'
        #storage = GCSStorage(project_id=self._project_id,credentials=self._gcs_credentials, bucket=self._bucket)
        new_file_id = self.fs.create(
            io.BytesIO(FILE_CONTENT),
            filename=filename,
            content_type='application/pdf'
        )

        assert new_file_id is not None
    
