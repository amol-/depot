from datetime import datetime
import io
import json
from typing import List
import uuid
from google.cloud import storage
from depot.io import utils
from depot.io.interfaces import FileStorage, StoredFile
from depot._compat import unicode_text, percent_encode, percent_decode
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
import os
from depot.utils import make_content_disposition
CANNED_ACL_PUBLIC_READ = 'public-read'
CANNED_ACL_PRIVATE = 'private'

class GCSStoredFile(StoredFile):
    def __init__(self, file_id, blob):
        _check_file_id(file_id)
        self._blob = blob
        self._closed = False
        metadata = blob.metadata or {}
        
        filename = metadata['x-depot-filename'] if 'x-depot-filename' in metadata else None
        if filename:
            filename = percent_decode(filename)
        #content_type = blob.content_type #metadata['x-depot-content-type']
        metadata_info = {'filename': filename,
                         'content_type': blob.content_type,
                         'content_length': blob.size,
                         'last_modified': None}

        try:
            last_modified = metadata['x-depot-modified']
            if last_modified:
                metadata_info['last_modified'] = datetime.strptime(last_modified,'%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        super(GCSStoredFile, self).__init__(file_id=file_id, **metadata_info)

    def read(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        
        if self._blob is not None:
            try:
                data = self._blob.download_as_bytes()
                return data
            except NotFound:
                return None
        else:
            return None

    def close(self, *args, **kwargs):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    @property
    def public_url(self):
        return self._blob.public_url

class BucketDriver(object):

    def __init__(self, bucket, prefix):
        self.bucket = bucket
        self._prefix = prefix

    def get_blob(self, blob_name):
        return self.bucket.get_blob('%s%s' % (self._prefix, blob_name))
    
    def blob(self, blob_name):
        return self.bucket.blob('%s%s' % (self._prefix, blob_name))

    def new_blob(self, blob_name):
        return self.bucket.blob('%s%s' % (self._prefix, blob_name))

    def list_blob_names(self):
        blobs = self.bucket.list_blobs(prefix=self._prefix)
        return [k.name[len(self._prefix):] for k in blobs]


class GCSStorage(FileStorage):
    def __init__(self, project_id=None, credentials=None, bucket=None, policy=None, storage_class=None, prefix=''):
        
        if  os.environ.get("STORAGE_EMULATOR_HOST"):
            client_options = {'api_endpoint': os.environ.get("STORAGE_EMULATOR_HOST")}
            self.client = storage.Client(client_options=client_options)
            self._policy = CANNED_ACL_PRIVATE
        else:
            if not credentials:
                if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
                if os.environ["GOOGLE_APPLICATION_CREDENTIALS"].endswith(".json"):
                    if not os.path.isfile(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
                        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable does not point to a file")
                    credentials = service_account.Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
                if not os.environ["GOOGLE_APPLICATION_CREDENTIALS"].endswith(".json"):
                    credentials = service_account.Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]))
            
            if not project_id:
                project_id = credentials.project_id 
            policy = policy or CANNED_ACL_PUBLIC_READ
            assert policy in [CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE], (
                "Key policy must be %s or %s" % (CANNED_ACL_PUBLIC_READ, CANNED_ACL_PRIVATE))
            self._policy = policy or CANNED_ACL_PUBLIC_READ
            self.client = storage.Client(project=project_id, credentials=credentials)

        
        # check if bucket exists
        try:
            bucket = self.client.get_bucket(bucket)
        except NotFound:
            bucket = self.client.create_bucket(bucket)

        self._storage_class = storage_class or 'STANDARD'
        self._prefix = prefix

        if policy == CANNED_ACL_PUBLIC_READ:
            self.set_bucket_public_iam(bucket)
        self._bucket_driver = BucketDriver(bucket, prefix)

    def get(self, file_or_id):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)
        blob = self._bucket_driver.get_blob(file_id)
        if blob is None or not blob.exists():
            raise IOError('File %s not existing' % file_id)
        return GCSStoredFile(file_id, blob)
    
    def set_bucket_public_iam(self,bucket,members: List[str] = ["allUsers"]):
        policy = bucket.get_iam_policy(requested_policy_version=3)
        policy.bindings.append(
            {"role": "roles/storage.objectViewer", "members": members}
        )
        bucket.set_iam_policy(policy)
        
    def __save_file(self,blob, content, filename, content_type=None):
        if filename:
            filename = percent_encode(filename, safe='!#$&+-.^_`|~', encoding='utf-8')
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
            can_seek_and_tell = True
            try:
                pos = content.tell()
                content.seek(pos)
            except:
                can_seek_and_tell = False
            if can_seek_and_tell:
                # check if content has name attribute
                if hasattr(content, 'name'):
                    blob.upload_from_filename(content.name, content_type=content_type)
                else:
                    blob.upload_from_file(content, content_type=content_type)
            else:
                blob.upload_from_string(content.read(), content_type=content_type)
        else:
            if isinstance(content, unicode_text):
                raise TypeError('Only bytes can be stored, not unicode')
            blob.upload_from_string(content, content_type=content_type)
        
        if self._policy == CANNED_ACL_PUBLIC_READ:
            try:
                blob.make_public()
            except NotFound:
                pass

    def create(self, content, filename=None, content_type=None):
        content, filename, content_type = self.fileinfo(content, filename, content_type)
        new_file_id = str(uuid.uuid1())
        blob = self._bucket_driver.new_blob(new_file_id)
        self.__save_file(blob, content, filename, content_type)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)

        content, filename, content_type = self.fileinfo(content, filename, content_type, lambda: self.get(file_id))
        blob = self._bucket_driver.blob(file_id)

        self.__save_file(blob, content, filename, content_type)
        return file_id

    def delete(self, file_or_id):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)
        blob = self._bucket_driver.blob(file_id)
        if blob.exists():
            generation_match_precondition = None
            blob.reload()
            generation_match_precondition = blob.generation
            blob.delete(if_generation_match=generation_match_precondition)

    def exists(self, file_or_id):
        file_id = self.fileid(file_or_id)
        _check_file_id(file_id)
        blob = self._bucket_driver.get_blob(file_id)
        return blob is not None

    def list(self):
        return self._bucket_driver.list_blob_names()
 
def _check_file_id(file_id):
    # Check that the given file id is valid, this also
    # prevents unsafe paths.
    try:
        uuid.UUID('{%s}' % file_id)
    except:
        raise ValueError('Invalid file id %s' % file_id)
