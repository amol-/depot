from typing import List
import uuid
from datetime import datetime
from google.cloud import storage
from depot.io import utils
from depot.io.interfaces import FileStorage, StoredFile
from depot._compat import unicode_text, percent_encode
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
import os
from depot.utils import make_content_disposition
CANNED_ACL_PUBLIC_READ = 'public-read'
CANNED_ACL_PRIVATE = 'private'

class GCSStoredFile(StoredFile):
    def __init__(self, file_id, blob):
        _check_file_id(file_id)

        self.blob = blob
        self._fileid = file_id
        self._closed = False

        metadata = blob.metadata or {}
        filename = metadata.get('x-depot-filename')
        content_type = metadata.get('x-depot-content-type')
        content_length = blob.size

        last_modified = None
        try:
            last_modified = metadata.get('x-depot-modified')
            if last_modified:
                last_modified = datetime.strptime(last_modified, '%Y-%m-%d %H:%M:%S')
        except:
            pass

        super(GCSStoredFile, self).__init__(file_id, filename, content_type, last_modified, content_length)
        self._pos = 0

    def read(self, n=-1):
        if self.closed:
            raise ValueError("I/O operation on closed file")

        if self._pos == 0:
            # If we are starting a new read, we need to get the latest generation of the blob
            self.blob = storage.Blob(self.blob.name, self.blob.bucket)
        
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
    def __init__(self, project_id=None, credentials=None, bucket=None, policy=None, storage_class=None, prefix=''):
        if not credentials:
            if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            credentials = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        
        if isinstance(credentials, dict):
            credentials = service_account.Credentials.from_service_account_info(credentials)
        elif isinstance(credentials, str):
            credentials = service_account.Credentials.from_service_account_file(credentials)
        else:
            credentials = credentials
        
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
        self._prefix = prefix

        if policy == CANNED_ACL_PUBLIC_READ:
            self.set_bucket_public_iam(self.bucket)

    def get(self, file_or_id):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)

        blob = self.bucket.blob(self._prefix+file_id)
        if not blob.exists():
            # TODO: Can we get rid of this extra exists check?
            raise IOError('File %s not existing' % file_id)

        blob.reload()
        return GCSStoredFile(file_id, blob)
    
    def set_bucket_public_iam(self, bucket, members=("allUsers", )):
        policy = bucket.get_iam_policy(requested_policy_version=3)
        policy.bindings.append(
            {"role": "roles/storage.objectViewer", "members": members}
        )
        bucket.set_iam_policy(policy)
        
    def __save_file(self,file_id, content, filename, content_type=None):
        if filename:
            filename = percent_encode(filename, safe='!#$&+-.^_`|~', encoding='utf-8')
        blob = self.bucket.blob(self._prefix+file_id)
        blob.content_type = content_type
        #blob.content_encoding = 'utf-8'
        #blob.cache_control = 'no-cache'
        blob.content_disposition = make_content_disposition('inline', filename)

        blob.metadata = {
            'x-depot-modified': utils.timestamp(),
            'x-depot-filename': filename,
            'x-depot-content-type': content_type
        }

        if hasattr(content, 'read'):
            try:
                pos = content.tell()
                content.seek(pos)
                blob.upload_from_file(content, content_type=content_type)
            except:
                content = content.read()
                blob.upload_from_string(content, content_type=content_type)
        else:
            if isinstance(content, unicode_text):
                raise TypeError('Only bytes can be stored, not unicode')
            blob.upload_from_string(content, content_type=content_type)
        
        if self._policy == CANNED_ACL_PUBLIC_READ:
            blob.make_public()

    def create(self, content, filename=None, content_type=None):
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        new_file_id = str(uuid.uuid4())
        self.__save_file(new_file_id, content, filename, content_type)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)
        
        existing_file = self.get(file_id)
        content, filename, content_type = self.fileinfo(content, filename, content_type, existing_file)
        self.__save_file(file_id, content, filename, content_type)

    def delete(self, file_or_id):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)

        blob = self.bucket.blob(self._prefix+file_id)
        generation_match_precondition = None
        try:
            blob.reload()
            generation_match_precondition = blob.generation
            blob.delete(if_generation_match=generation_match_precondition)
        except NotFound:
            pass

    def exists(self, file_or_id):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)

        blob = self.bucket.blob(self._prefix+file_id)
        return blob.exists()

    def list(self):
        return [blob.name for blob in self.bucket.list_blobs()]


def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        uuid.UUID('{%s}' % file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)