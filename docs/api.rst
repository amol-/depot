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

.. autoclass:: depot.fields.interfaces.DepotFileInfo
    :members:

.. autoclass:: depot.fields.interfaces.FileFilter
    :members:

.. autoclass:: depot.fields.upload.UploadedFile
    :members:
    :inherited-members:


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
