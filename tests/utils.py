import cgi
import tempfile


class OpenFiles:
    def __init__(self):
        self._files = []

    def open(self, *args, **kwargs):
        f = open(*args, **kwargs)
        self._files.append(f)
        return f

    def add(self, f):
        self._files.append(f)
        return f

    def close_all(self):
        for f in self._files:
            f.close()
        self._files = []


def create_cgifs(mimetype, content, filename):
    fs = cgi.FieldStorage()
    fs.filename = filename
    fs.type = mimetype

    if hasattr(content, 'read'):
        fs.file = content
    else:
        fs.file = tempfile.NamedTemporaryFile(mode='w+b')
        fs.file.write(content)

    fs.file.seek(0)
    return fs