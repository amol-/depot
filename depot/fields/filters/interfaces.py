from abc import ABCMeta
from depot._compat import with_metaclass


class FileFilter(with_metaclass(ABCMeta, object)):
    def on_save(self, uploaded_file):
        pass