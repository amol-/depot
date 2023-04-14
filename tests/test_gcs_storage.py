import io
import os
import uuid
import requests
from flaky import flaky
from nose import SkipTest
from google.cloud.exceptions import NotFound

from depot._compat import PY2, unicode_text
from depot.io.gcs import GCSStorage

FILE_CONTENT = b'HELLO WORLD'


@flaky
class TestGCSStorage(object):
    @classmethod
    def setupClass(self):
        self.run_id = '%s-%s' % (uuid.uuid1().hex, os.getpid())
        self._prefix = 'test-'

        try:
            global GCSStorage
            from depot.io.gcs import GCSStorage
        except ImportError:
            raise SkipTest('Google Cloud Storage not installed')

        env = os.environ
        google_application_credentials = env.get('GOOGLE_APPLICATION_CREDENTIALS')
        if google_application_credentials is None:
            raise SkipTest('Google Cloud Storage credentials not available')

        self._bucket = 'filedepot-testfs-%s' % self.run_id
        
        # get project id from credentials
        with open(google_application_credentials) as f:
            import json
            project_id = json.load(f)['project_id']
        self._project_id = project_id
        if project_id is None:
            raise SkipTest('Google Cloud Storage project id not available')

        self.fs = GCSStorage(project_id=self._project_id,credentials=google_application_credentials, bucket=self._bucket, prefix=self._prefix)

    @classmethod
    def teardownClass(self):
        for blob in self.fs.bucket.list_blobs(prefix=self._prefix):
            blob.delete()

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
        storage = GCSStorage(project_id=self._project_id, bucket=self._bucket)
        new_file_id = storage.create(
            io.BytesIO(FILE_CONTENT),
            filename=filename,
            content_type='application/pdf'
        )

        assert new_file_id is not None
    
