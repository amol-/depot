# -*- coding: utf-8 -*-
from .._compat import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from io import IOBase
import cgi
import os
import mimetypes


class StoredFile(IOBase):
    """Interface for already saved files.

    Already stored files can only be read back, so they subclass io.RawIOBase and require
    to only provide ``readinto(self, b)`` method so that they can be read back.

    To replace/overwrite a file content do not try to call the ``write`` method,
    instead use the storage backend to replace the file content.
    """
    def __init__(self, file_id, filename=None, content_type=None, last_modified=None):
        self.file_id = file_id
        self.filename = filename
        self.content_type = content_type
        self.last_modified = last_modified

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return False

    @property
    def name(self):
        return self.filename

    @abstractmethod
    def read(self, n=-1):  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def close(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    @abstractproperty
    def closed(self):  # pragma: no cover
        raise NotImplementedError

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
        return getattr(file_or_id, 'file_id', file_or_id)

    @staticmethod
    def fileinfo(fileobj, filename=None, content_type=None):
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

        if  content_type is None:
            if filename is not None:
                content_type = mimetypes.guess_type(filename, strict=False)[0]
            content_type = content_type or 'application/octet-stream'

        return content, filename, content_type

    @abstractmethod
    def get(self, file_or_id):  # pragma: no cover
        """Opens the file given by its unique id.

        This operation is guaranteed to return
        a ``StoredFile`` instance.
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, content, filename=None, content_type=None):  # pragma: no cover
        """Saves a new file

        """
        raise NotImplementedError

    @abstractmethod
    def replace(self, file_or_id, content, filename=None, content_type=None):  # pragma: no cover
        """Replaces an existing file

        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, file_or_id):  # pragma: no cover
        """
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, file_or_id):  # pragma: no cover
        """
        """
        raise NotImplementedError