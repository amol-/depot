
.. image:: https://raw.github.com/amol-/depot/master/docs/_static/logo.png

DEPOT - File Storage Made Easy
==============================

.. image:: https://travis-ci.org/amol-/depot.png?branch=master 
    :target: https://travis-ci.org/amol-/depot 

.. image:: https://coveralls.io/repos/amol-/depot/badge.png?branch=master
    :target: https://coveralls.io/r/amol-/depot?branch=master 

.. image:: https://img.shields.io/pypi/v/filedepot.svg
   :target: https://pypi.python.org/pypi/filedepot

.. image:: https://img.shields.io/pypi/dm/filedepot.svg
   :target: https://pypi.python.org/pypi/filedepot

DEPOT is a framework for easily storing and serving files in
web applications on Python2.6+ and Python3.2+.

Installing
----------

Installing DEPOT can be done from PyPi itself by installing the ``filedepot`` distribution::

    $ pip install filedepot

Getting Started
---------------

To start using Depot refer to `Documentation <https://depot.readthedocs.io/en/latest/>`_

DEPOT was `presented at PyConUK and PyConFR <http://www.slideshare.net/__amol__/pyconfr-2014-depot-story-of-a-filewrite-gone-wrong>`_ in 2014

Here is a simple example of using depot standalone to store files on MongoDB::

    from depot.manager import DepotManager

    # Configure a *default* depot to store files on MongoDB GridFS
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.gridfs.GridFSStorage',
        'depot.mongouri': 'mongodb://localhost/db'
    })

    depot = DepotManager.get()

    # Save the file and get the fileid
    fileid = depot.create(open('/tmp/file.png'))

    # Get the file back
    stored_file = depot.get(fileid)
    print stored_file.filename
    print stored_file.content_type

ChangeLog
---------

0.3.1
~~~~~

* Fixed ``Content-Disposition`` header when serving from S3 directly
* Fixed size of SQLAlchemy field on Oracle (was bigger than the allowed maximum)

0.3.0
~~~~~

- ``MemoryFileStorage`` provides in memory storage for files. This is meant to provide a
  convenient way to speed up test suites and avoid fixture clean up issues.
- S3Storage can now generate public urls for private files (expire in 1 year)
- Files created from plain bytes are now named "unnamed" instead of missing a filename.

0.2.1
~~~~~

- ``S3Storage`` now supports the ``prefix`` option to store files in a subpath

0.2.0
~~~~~

- Storages now provide a ``list`` method to list files available on the store (This is not meant to be used to retrieve files uploaded by depot as it lists all the files).
- ``DepotExtension`` for Ming is now properly documented

0.1.2
~~~~~

- It is now possible to use multiple ``WithThumbnailFilter`` to generate multiple thumbnails
  with different resolutions.
- Better documentation for MongoDB ``UploadedFileProperty`` 

0.1.1
~~~~~

- Fixed a bug with Ming support when acessing ``UploadedFileProperty`` as a class property
- Improved support for DEPOT inside TurboGears admin when using MongoDB

0.1.0
~~~~~

- Added ``DepotManager.alias`` to configure aliases to storage.
  This allows easy migration from one storage to another by switching where the alias points.
- Now ``UploadedFileField`` permits to specify ``upload_storage`` to link a Model Column to a specific storage.
- Added ``policy`` and ``encrypt_key`` options to `S3Storage` to upload private and encrypted files.

0.0.6
~~~~~

- Added `host` option to `S3Storage` to allow using providers different from *AWS*.

0.0.5
~~~~~

- Added `FileIntent` to explicitly provide `content_type` and `filename` to uploaded content.

0.0.4
~~~~~

- Added Content-Disposition header with original filename in WSGI middleware

0.0.3
~~~~~

- Work-Around for issue with `wsgi.file_wrapper` provided by Waitress WSGI Server

0.0.2
~~~~~

- Official Support for AWS S3 on Python3
