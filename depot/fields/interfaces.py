from abc import ABCMeta, abstractmethod
from depot._compat import with_metaclass
from depot.manager import DepotManager


class FileFilter(with_metaclass(ABCMeta, object)):
    """Interface that must be implemented by file filters.

    File filters get executed whenever a file is stored on the database
    using one of the supported fields. Can be used to add additional data
    to the stored file or change it. When file filters are run the file
    has already been stored.

    """
    @abstractmethod
    def on_save(self, uploaded_file):
        """Filters are required to provide their own implementation"""
        return


class DepotFileInfo(with_metaclass(ABCMeta, dict)):
    """Keeps informations on a content related to a specific depot.

    By itself the DepotFileInfo does nothing, it is required to implement
    a :meth:`process_content` method that actually saves inside the
    file info the information related to the content. The only information
    which is saved by default is the depot name itself.

    It is a specialized dictionary that provides also attribute style access,
    the dictionary parent permits easy encoding/decoding to most marshalling
    systems.

    """
    def __init__(self, content, depot_name=None):
        super(DepotFileInfo, self).__init__()

        if isinstance(content, dict):
            object.__setattr__(self, 'original_content', None)
            self.update(content)
        else:
            object.__setattr__(self, 'original_content', content)
            if depot_name is None:
                depot_name = DepotManager.get_default()

            self['depot_name'] = depot_name
            self['files'] = []
            self.process_content(content)

    @abstractmethod
    def process_content(self, content, filename=None, content_type=None):
        """Process content in the given depot.

        This is implemented by subclasses to provide some kind of behaviour on the
        content in the related Depot. The default implementation is provided by
        :class:`depot.fields.upload.UploadedFile` which stores the content into
        the depot.

        """
        return

    def __getitem__(self, key):
        return  dict.__getitem__(self, key)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    __setattr__ = dict.__setitem__

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)
