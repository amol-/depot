from typing import List
import uuid
from google.cloud import storage
from depot.io import utils
from depot.io.interfaces import FileStorage, StoredFile
from depot._compat import unicode_text, percent_encode, percent_decode
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
import datetime
import os

from depot.utils import make_content_disposition
CANNED_ACL_PUBLIC_READ = 'public-read'
CANNED_ACL_PRIVATE = 'private'

class GCSStoredFile(StoredFile):
    def __init__(self, file_id, blob):
        self.blob = blob
        self._fileid = file_id
        self._closed = False

        metadata = blob.metadata or {}
        filename = metadata.get('x-depot-filename')
        content_type = metadata.get('x-depot-content-type')

        last_modified = blob.updated
        content_length = blob.size

        super(GCSStoredFile, self).__init__(file_id, filename, content_type, last_modified, content_length)
        self._pos = 0

    def read(self, n=-1):
        if self.closed:
            raise ValueError("I/O operation on closed file")

        data = self.blob.download_as_bytes(start=self._pos, end=self._pos + n - 1 if n != -1 else None)
        self._pos += len(data)
        return data

    def close(self, *args, **kwargs):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    @property
    def public_url(self):
        return self.blob.public_url


class GCSStorage(FileStorage):
    def __init__(self, project_id=None, credentials=None, bucket=None, policy=None, storage_class=None):
        
        # added support for local emulator
        if os.getenv("STORAGE_EMULATOR_HOST"):
            client_options = {}
            client_options["api_endpoint"] = os.getenv("STORAGE_EMULATOR_HOST")
            self.client = storage.Client(client_options=client_options)
        else:
            if not credentials:
                if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
                credentials = service_account.Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
            if not project_id:
                project_id = credentials.project_id 
            policy = policy or CANNED_ACL_PUBLIC_READ
            assert policy in [CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE], (
                "Key policy must be %s or %s" % (CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE))
            self.client = storage.Client(project=project_id, credentials=credentials)

        
        # check if bucket exists
        try:
            self.bucket = self.client.get_bucket(bucket)
        except NotFound:
            self.bucket = self.client.create_bucket(bucket)

        self._policy = policy or CANNED_ACL_PUBLIC_READ
        self._storage_class = storage_class or 'STANDARD'

        if policy == CANNED_ACL_PUBLIC_READ:
            self.set_bucket_public_iam(self.bucket)

    def get(self, file_or_id):
        file_id = self.fileid(file_or_id)
        blob = self.bucket.blob(file_id)
        if not blob.exists():
            raise NotFound('File %s not existing' % file_id)
        return GCSStoredFile(file_id, blob)
    
    def set_bucket_public_iam(self,bucket,members: List[str] = ["allUsers"]):
        policy = bucket.get_iam_policy(requested_policy_version=3)
        policy.bindings.append(
            {"role": "roles/storage.objectViewer", "members": members}
        )
        bucket.set_iam_policy(policy)
        
    def __save_file(self,file_id, content, filename, content_type=None):
        if filename:
            filename = percent_encode(filename, safe='!#$&+-.^_`|~', encoding='utf-8')
        blob = self.bucket.blob(file_id)
        blob.content_type = content_type
        #blob.content_encoding = 'utf-8'
        #blob.cache_control = 'no-cache'
        blob.content_disposition = make_content_disposition('inline', filename)
        
        blob.metadata = {
            'x-depot-modified': utils.timestamp(),
            'x-depot-filename': filename,
            'x-depot-content-type': content_type
        }
        
        blob.upload_from_file(content, content_type=content_type)
        
        if self._policy == CANNED_ACL_PUBLIC_READ:
            blob.make_public()

    def create(self, content, filename=None, content_type=None):
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        new_file_id = str(uuid.uuid4())
        self.__save_file(new_file_id, content, filename, content_type)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        file_id = self.fileid(file_or_id)
        existing_file = self.get(file_id)
        content, filename, content_type = self.fileinfo(content, filename, content_type, existing_file)
        
        new_file_id = str(uuid.uuid4())
        if new_file_id != file_id:
            raise ValueError("New file ID does not match existing file ID")

        self.__save_file(new_file_id, content, filename, content_type)

    def delete(self, file_or_id):
        file_id = self.fileid(file_or_id)
        blob = self.bucket.blob(file_id)
        generation_match_precondition = None
        blob.reload()
        generation_match_precondition = blob.generation
        blob.delete(if_generation_match=generation_match_precondition)

    def exists(self, file_or_id):
        file_id = self.fileid(file_or_id)
        blob = self.bucket.blob(file_id)
        return blob.exists()

    def list(self):
        return [blob.name for blob in self.bucket.list_blobs()]
