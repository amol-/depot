
.. image:: https://raw.github.com/amol-/depot/master/docs/_static/logo.png

DEPOT - File Storage Made Easy
==============================

.. image:: https://travis-ci.org/amol-/depot.png?branch=master 
    :target: https://travis-ci.org/amol-/depot 

.. image:: https://coveralls.io/repos/amol-/depot/badge.png?branch=master
    :target: https://coveralls.io/r/amol-/depot?branch=master 

.. image:: https://pypip.in/v/filedepot/badge.png
   :target: https://pypi.python.org/pypi/filedepot

.. image:: https://pypip.in/d/filedepot/badge.png
   :target: https://pypi.python.org/pypi/filedepot

DEPOT is a framework for easily storing and serving files in
web applications on Python2.6+ and Python3.2+.

Installing
----------

Installing DEPOT can be done from PyPi itself by installing the ``filedepot`` distribution::

    $ pip install filedepot

Getting Started
---------------

To start using Depot refer to `Documentation <http://depot.readthedocs.org/en/latest/>`_

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

0.0.4
~~~~~

- Added Content-Disposition header with original filename in WSGI middleware

0.0.3
~~~~~

- Work-Around for issue with `wsgi.file_wrapper` provided by Waitress WSGI Server

0.0.2
~~~~~

- Official Support for AWS S3 on Python3
