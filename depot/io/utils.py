import cgi
from datetime import datetime
from io import BytesIO
from depot._compat import byte_string


def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def file_from_content(content):
    f = content
    if isinstance(content, cgi.FieldStorage):
        f = content.file
    elif isinstance(content, byte_string):
        f = BytesIO(content)
    f.seek(0)
    return f