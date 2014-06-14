from depot.manager import DepotManager
from .interfaces import DepotFileInfo
import json


class UploadedFile(DepotFileInfo):
    """Simple :class:`DepotFileInfo` implementation that stores plain files.

    Takes a file as content and uploads it to the depot while saving around
    most file informations. Pay attention that if the file gets replaced
    through the depot the ``UploadedFile`` will continue to have the old data.

    Also provides support for encoding/decoding using JSON for storage inside
    databases as a plain string.

    Default attributes provided for all ``UploadedFile`` include:
        - filename     - This is the name of the uploaded file
        - file_id      - This is the ID of the uploaded file
        - path         - This is a depot_name/file_id path which can
                         be used with :meth:`DepotManager.get_file` to retrieve the file
        - content_type - This is the content type of the uploaded file
        - uploaded_at  - This is the upload date in YYYY-MM-DD HH:MM:SS format
        - url          - Public url of the uploaded file
        - file         - The :class:`depot.io.interfaces.StoredFile` instance of the stored file
    """
    def process_content(self, content):
        file_path, file_id = self.store_content(content)
        self['file_id'] = file_id
        self['path'] = file_path

        saved_file = self.file
        self['filename'] = saved_file.filename
        self['content_type'] = saved_file.content_type
        self['uploaded_at'] = saved_file.last_modified.strftime('%Y-%m-%d %H:%M:%S')
        self['_public_url'] = saved_file.public_url

    def store_content(self, content, filename=None):
        file_id = self.depot.create(content, filename)
        file_path = '%s/%s' % (self.depot_name, file_id)
        self.files.append(file_path)
        return file_path, file_id

    def encode(self):
        return json.dumps(self)

    @classmethod
    def decode(cls, data):
        return cls(json.loads(data))

    @property
    def url(self):
        public_url = self['_public_url']
        if public_url:
            return public_url
        return DepotManager.get_middleware().url_for(self['path'])

    @property
    def depot(self):
        return DepotManager.get(self.depot_name)

    @property
    def file(self):
        return self.depot.get(self.file_id)