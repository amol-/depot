import cgi
import tempfile


def create_cgifs(mimetype, content, filename):
    fs = cgi.FieldStorage()
    fs.filename = filename
    fs.type = mimetype

    if hasattr(content, 'read'):
        fs.file = content
    else:
        fs.file = tempfile.TemporaryFile(mode='w+b')
        fs.file.write(content)

    fs.file.seek(0)
    return fs