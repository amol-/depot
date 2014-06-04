# -*- coding: utf-8 -*-
from filedepot._compat import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from io import RawIOBase


class StoredFile(RawIOBase):
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

    @abstractmethod
    def readinto(self, b):
        raise NotImplementedError


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

    @abstractmethod
    def get(self, file_or_id):
        """Opens the file given by its unique id.

        This operation is guaranteed to return
        a ``StoredFile`` instance.
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, content, filename, content_type=None):
        """Saves a new file

        """
        raise NotImplementedError

    @abstractmethod
    def replace(self, file_or_id, content, filename, content_type=None):
        """Replaces an existing file

        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, file_or_id):
        """
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, file_or_id):
        """
        """
        raise NotImplementedError