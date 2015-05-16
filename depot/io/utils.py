import cgi
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