from abc import ABCMeta
import cgi
from depot._compat import with_metaclass, unicode_text, byte_string
from io import BytesIO


class FileFilter(with_metaclass(ABCMeta, object)):
    @staticmethod
    def content_file(content):
        f = content
        if isinstance(content, cgi.FieldStorage):
            f = content.file
        elif isinstance(content, byte_string):
            f = BytesIO(content)
        f.seek(0)
        return f

    def before_save(self, content):
        return content

    def after_save(self, content, field_data):
        pass