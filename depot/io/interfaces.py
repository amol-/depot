"""General interface provided by all storage backends implemented in DEPOT.

Each storage backend is required to respect those classes and implement
the abstractmethods.

"""
from .._compat import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from io import IOBase
import cgi
import os
import mimetypes
from depot.io.utils import FileIntent


class StoredFile(IOBase):
    """Interface for already saved files.

    It provides metadata on the stored file through following properties:
        - file_id
        - filename
        - content_type
        - last_modified
        - content_length

    Already stored files can only be read back, so they are required to only provide
    ``read(self, n=-1)``, ``close()`` methods and ``closed`` property so that they
    can be read.

    To replace/overwrite a file content do not try to call the ``write`` method,
    instead use the storage backend to replace the file content.
    """
    def __init__(self, file_id, filename=None, content_type=None, last_modified=None,
                 content_length=None):
        self.file_id = file_id
        self.filename = filename
        self.content_type = content_type
        self.last_modified = last_modified
        self.content_length = content_length

    def readable(self):
        """Returns if the stored file is readable or not

        Usually all stored files are readable
        """
        return True

    def writable(self):
        """Returns if the stored file is writable or not

        Stored files are not writable, you should rely on the relative
        :class:`FileStorage` to overwrite their content
        """
        return False

    def seekable(self):
        """Returns if the stored file is seekable or not

        By default stored files are not seekable
        """
        return False

    @property
    def name(self):
        """This is the filename of the saved file

        If a filename was not available when the file was created
        this will return "unknown" as filename.
        """
        return self.filename

    @abstractmethod
    def read(self, n=-1):  # pragma: no cover
        """Reads ``n`` bytes from the file.

        If ``n`` is not specified or is ``-1`` the whole
        file content is read in memory and returned
        """
        return

    @abstractmethod
    def close(self, *args, **kwargs):  # pragma: no cover
        """Closes the file.

        After closing the file it won't be possible to read
        from it anymore. Some implementation might not do anything
        when closing the file, but they still are required to prevent
        further reads from a closed file.
        """
        return

    @abstractproperty
    def closed(self):  # pragma: no cover
        """Returns if the file has been closed.

        When ``closed`` return ``True`` it won't be possible
        to read anoymore from this file.
        """
        return

    @property
    def public_url(self):
        """The public HTTP url from which file can be accessed.

        When supported by the storage this will provide the
        public url to which the file content can be accessed.
        In case this returns ``None`` it means that the file can
        only be served by the :class:`DepotMiddleware` itself.
        """
        return None

    def __repr__(self):
        return '<%s:%s filename=%s content_type=%s last_modified=%s>' % (self.__class__.__name__,
                                                                         self.file_id,
                                                                         self.filename,
                                                                         self.content_type,
                                                                         self.last_modified)


class FileStorage(with_metaclass(ABCMeta, object)):
    """Interface for storage providers.

    The FileStorage base class declares a standard interface for storing and retrieving files
    in an underlying storage system.

    Each storage system implementation is required to provide this interface to correctly work
    with filedepot.
    """

    @staticmethod
    def fileid(file_or_id):
        """Gets the ID of a given :class:`StoredFile`

        If the given parameter is already a StoredFile id it will
        directly return it.
        """
        return getattr(file_or_id, 'file_id', file_or_id)

    @staticmethod
    def fileinfo(fileobj, filename=None, content_type=None):
        """Tries to extract from the given input the actual file object, filename and content_type

        This is used by the create and replace methods to correctly deduce their parameters
        from the available information when possible.
        """
        if isinstance(fileobj, FileIntent):
            return fileobj.fileinfo

        content = fileobj
        if isinstance(fileobj, cgi.FieldStorage):
            content = fileobj.file

        if filename is None:
            if getattr(fileobj, 'filename', None) is not None:
                filename = fileobj.filename
            elif getattr(fileobj, 'name', None) is not None:
                filename = os.path.basename(fileobj.name)

        if content_type is None:
            if getattr(fileobj, 'content_type', None) is not None:
                content_type = fileobj.content_type
            elif getattr(fileobj, 'type', None) is not None:
                content_type = fileobj.type

        if content_type is None:
            if filename is not None:
                content_type = mimetypes.guess_type(filename, strict=False)[0]
            content_type = content_type or 'application/octet-stream'

        return content, filename, content_type

    @abstractmethod
    def get(self, file_or_id):  # pragma: no cover
        """Opens the file given by its unique id.

        This operation is guaranteed to return
        a :class:`StoredFile` instance or should raise ``IOError``
        if the file is not found.
        """
        return

    @abstractmethod
    def create(self, content, filename=None, content_type=None):  # pragma: no cover
        """Saves a new file and returns the ID of the newly created file.

        ``content`` parameter can either be ``bytes``, another ``file object``
        or a :class:`cgi.FieldStorage`. When ``filename`` and ``content_type``
        parameters are not provided they are deducted from the content itself.
        """
        return

    @abstractmethod
    def replace(self, file_or_id, content, filename=None, content_type=None):  # pragma: no cover
        """Replaces an existing file, an ``IOError`` is raised if the file didn't already exist.

        Given a :class:`StoredFile` or its ID it will replace the current content
        with the provided ``content`` value. If ``filename`` and ``content_type`` are
        provided or can be deducted by the ``content`` itself they will also replace
        the previous values, otherwise the current values are kept.
        """
        return

    @abstractmethod
    def delete(self, file_or_id):  # pragma: no cover
        """Deletes a file. If the file didn't exist it will just do nothing."""
        return

    @abstractmethod
    def exists(self, file_or_id):  # pragma: no cover
        """Returns if a file or its ID still exist."""
        return
