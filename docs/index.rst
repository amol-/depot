DEPOT - File Storage Made Easy
==============================

Welcome to the DEPOT Documentation.
DEPOT is a framework for easily storing and serving files in
web applications on Python2.6+ and Python3.2+.

Depot can be used :ref:`Standalone <depot_standalone>` or
:ref:`with your ORM <depot_with_your_orm>` to quickly provide
attachment support to your model.

Modern web applications need to rely on a huge amount of
stored images, generated files and other data which is usually
best to keep outside of your database. DEPOT provides a
simple and effective interface for storing your files on
a storage backend at your choice (**Local**, **S3**, **GridFS**)
and easily relate them to your application models (**SQLAlchemy**, **Ming**)
like you would for plain data.

Depot is a swiss army knife for files that provides:

    - Multiple backends: Store your data on GridFS or S3 with a *single API*
    - In Memory storage :class:`depot.io.memory.MemoryFileStorage` provided for tests suite.
      Provides faster tests and no need to clean-up fixtures.
    - Meant for *Evolution*: Change the backend anytime you want, old data will continue to work
    - Integrates with your *ORM*: When using SQLAlchemy, attachments are handled like a
      plain model attribute. It's also *session ready*: Rollback causes the files to be deleted.
    - Smart *File Serving*: When the backend already provides a public HTTP endpoint (like S3)
      the WSGI :class:`depot.middleware.DepotMiddleware` will redirect to the public address
      instead of loading and serving the files by itself.
    - Flexible: The :class:`depot.manager.DepotManager` will handle configuration,
      middleware creation and files for your application, but if you want you can manually
      create multiple depots or middlewares without using the manager.

DEPOT was presented at PyConUK 2014 and PyConFR 2014, for a short presentation
you can have a look at the PyConFR slides:

.. raw:: html

    <iframe src="//www.slideshare.net/slideshow/embed_code/40711828" width="510" height="420" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe>

.. _installing_depot:

Installing Depot
----------------

Installing DEPOT can be done from PyPi itself by installing the ``filedepot`` distribution::

    $ pip install filedepot

Keep in mind that DEPOT itself has no dependencies, if you want to use GridFS storage,
S3 or any other storage that requires third party libraries, your own application is
required to install the dependency. In this specific case ``pymongo`` and ``boto``
are respectively needed for GridFS and S3 support.

.. _depot_standalone:

Depot Standalone
----------------

Depot can easily be used to save and retrieve files in any Python script,
Just get a depot using the :class:`depot.manager.DepotManager` and store the files.
With each file, additional data commonly used in HTTP like *last_modified*,
*content_type* and so on is stored. This data is available inside the
:class:`depot.io.interfaces.StoredFile` which is returned when getting the file back:

.. code-block:: python

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

Depot with your WebFramework
----------------------------

To start using DEPOT with your favourite Web Framework you can have a look at
the `web framework examples <https://github.com/amol-/depot/tree/master/examples>`_
and read the :ref:`DEPOT for Web <depot_for_web>` guide.

.. _depot_with_your_orm:

Attaching Files to Models
-------------------------

Depot also features simple integration with SQLAlchemy by providing customized
model field types for storing files attached to your ORM document.
Just declare columns with these types inside your models and assign the files:

.. code-block:: python

    from depot.fields.sqlalchemy import UploadedFileField
    from depot.fields.specialized.image import UploadedImageWithThumb


    class Document(Base):
        __tablename__ = 'document'

        uid = Column(Integer, autoincrement=True, primary_key=True)
        name = Column(Unicode(16), unique=True)
        content = Column('content_col', UploadedFileField)  # plain attached file

        # photo field will automatically generate thumbnail
        photo = Column(UploadedFileField(upload_type=UploadedImageWithThumb))


    # Store documents with attached files, the source can be a file or bytes
    doc = Document(name=u'Foo',
                   content=b'TEXT CONTENT STORED AS FILE',
                   photo=open('/tmp/file.png'))
    DBSession.add(doc)
    DBSession.flush()

    # DEPOT is session aware, commit/rollback to keep or delete the stored files.
    DBSession.commit()

Fetching back the attachments is as simple as fetching back the documents
themselves::

    d = DBSession.query(Document).filter_by(name=u'Foo').first()
    print d.content.file.read()
    print d.photo.url
    print d.photo.thumb_url

In case the backend doesn't already provide HTTP serving of the files
you can use the DepotMiddleware to serve them in your application::

    wsgiapp = DepotManager.make_middleware(wsgiapp)


User Guide
==========

.. toctree::
   :maxdepth: 2

   userguide
   database


API Reference
=============

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api
