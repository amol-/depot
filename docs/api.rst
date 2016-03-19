.. _api:

API Reference
===============

This part of the documentation covers all the public classes in Depot.

Application Support
-----------------------

.. autoclass:: depot.manager.DepotManager
    :members:

.. autoclass:: depot.middleware.DepotMiddleware
    :members:


Database Support
----------------------

.. module:: depot.fields

.. autoclass:: depot.fields.sqlalchemy.UploadedFileField
    :members:

.. autoclass:: depot.fields.ming.UploadedFileProperty
    :members:

.. autoclass:: depot.fields.ming.DepotExtension
    :members:

.. autoclass:: depot.fields.interfaces.DepotFileInfo
    :members:

.. autoclass:: depot.fields.interfaces.FileFilter
    :members:

.. autoclass:: depot.fields.upload.UploadedFile
    :members:

Filters
~~~~~~~

.. module:: depot.fields.filters

.. autoclass:: depot.fields.filters.thumbnails.WithThumbnailFilter

Specialized FileTypes
~~~~~~~~~~~~~~~~~~~~~

.. module:: depot.fields.specialized

.. autoclass:: depot.fields.specialized.image.UploadedImageWithThumb


Storing Files
------------------------

.. module:: depot.io.interfaces

.. autoclass:: StoredFile
   :members:
   :inherited-members:

.. autoclass:: FileStorage
   :members:
   :inherited-members:

.. autoclass:: depot.io.local.LocalFileStorage
    :members:

.. autoclass:: depot.io.gridfs.GridFSStorage
    :members:

.. autoclass:: depot.io.awss3.S3Storage
    :members:

.. autoclass:: depot.io.memory.MemoryFileStorage
    :members:

Utilities
---------

.. autofunction:: depot.io.utils.file_from_content

.. autoclass:: depot.io.utils.FileIntent