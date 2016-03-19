import cgi
import mimetypes
import os
from datetime import datetime
from tempfile import SpooledTemporaryFile
from depot._compat import byte_string


INMEMORY_FILESIZE = 1024*1024


def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def file_from_content(content):
    """Provides a real file object from file content

    Converts ``FileStorage``, ``FileIntent`` and
    ``bytes`` to an actual file.
    """
    f = content
    if isinstance(content, cgi.FieldStorage):
        f = content.file
    elif isinstance(content, FileIntent):
        f = content._fileobj
    elif isinstance(content, byte_string):
        f = SpooledTemporaryFile(INMEMORY_FILESIZE)
        f.write(content)
    f.seek(0)
    return f


class FileIntent(object):
    """Represents the intention to upload a file

    Whenever a file can be stored by depot, a FileIntent
    can be passed instead of the file itself. This permits
    to easily upload objects that are not files or to add
    missing information to the uploaded files.
    """
    def __init__(self, fileobj, filename, content_type):
        self._fileobj = fileobj
        self._filename = filename
        self._content_type = content_type

    @property
    def fileinfo(self):
        return self._fileobj, self._filename, self._content_type


class _FileInfo(object):
    """Utility class to get a file object, filename and content_type from available data.

    This is used by most Storage to convert data to a file like object, to
    find a meaningful filename for the file and to detect the content type of the
    file.
    """
    DEFAULT_CONTENT_TYPE = 'application/octet-stream'
    DEFAULT_NAME = 'unnamed'

    def __init__(self, fileobj, filename=None, content_type=None):
        self._content, self._filename, self._content_type = self._resolve(fileobj,
                                                                          filename,
                                                                          content_type)

    def get_info(self, existing=None):
        if self._filename is None and existing is not None:
            if callable(existing):
                existing = existing()
            return self._content, existing.filename, existing.content_type

        return (
            self._content,
            self._filename or self.DEFAULT_NAME,
            self._content_type or self.DEFAULT_CONTENT_TYPE
        )

    def _resolve(self, fileobj, filename, content_type):
        if isinstance(fileobj, FileIntent):
            return fileobj.fileinfo

        content = self._get_content_from_file_obj(fileobj)
        filename = filename or self._get_filename_from_fileob(fileobj)
        content_type = content_type or self._get_content_type_from_fileobj(fileobj)

        if content_type is None and filename is not None:
            content_type = mimetypes.guess_type(filename, strict=False)[0]

        return content, filename, content_type

    def _get_content_from_file_obj(self, fileobj):
        if isinstance(fileobj, cgi.FieldStorage):
            return fileobj.file
        return fileobj

    def _get_filename_from_fileob(self, fileobj):
        if getattr(fileobj, 'filename', None) is not None:
            return fileobj.filename
        elif getattr(fileobj, 'name', None) is not None:
            return os.path.basename(fileobj.name)

    def _get_content_type_from_fileobj(self, fileobj):
        if getattr(fileobj, 'content_type', None) is not None:
            return fileobj.content_type
        elif getattr(fileobj, 'type', None) is not None:
            return fileobj.type
