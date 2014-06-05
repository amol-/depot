import cgi
import tempfile


def create_cgifs(mimetype, content, filename):
    fs = cgi.FieldStorage()
    fs.filename = filename
    fs.file = tempfile.TemporaryFile(mode='w+b')
    fs.type = mimetype
    fs.file.write(content)
    fs.file.seek(0)
    return fs