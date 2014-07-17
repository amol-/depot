import cgi
from datetime import datetime
from tempfile import SpooledTemporaryFile
from depot._compat import byte_string


INMEMORY_FILESIZE = 1024*1024


def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def file_from_content(content):
    f = content
    if isinstance(content, cgi.FieldStorage):
        f = content.file
    elif isinstance(content, byte_string):
        f = SpooledTemporaryFile(INMEMORY_FILESIZE)
        f.write(content)
    f.seek(0)
    return f