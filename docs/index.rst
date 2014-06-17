
DEPOT - File Storage made Easy
=========================================

Welcome to DEPOT Documentation, DEPOT is an framework
for easily storing and serving files in web applications.

Modern web applications need to rely on a huge amount of
stored images, generated files and other data which is usually
best to keep outside of your database. DEPOT provides a
simple and effective interface for storing your files on
a storage backend at your choice (**Local**, **S3**, **GridFS**)
and easily relate them to your application models (**SQLAlchemy**, **Ming**)
like you would for plain data.

Depot is a swiss army knife for files that provides:

    - Multiple backends: Store your data on GridFS or S3 with a *single API*
    - Meant for *Evolution*: Change backend when you want, old data will continue to work
    - Integrates with your *ORM*: When using SQLAlchemy attachments are handled like a
        plain model attribute. It's also *session ready* rollback causes the files to be deleted.
    - Smart *File Serving*: When the backend already provides a public HTTP endpoint (like S3)
        the WSGI :class:`depot.middleware.DepotMiddleware` will serve it instead of loading the files.
    - Flexible: The :class:`depot.manager.DepotManager` will handle configuration,
        middleware creation and files for your application, but if you want you can manually
        create multiple depots or middlewares without using the manager.

Depot can be used :ref:`Standalone <depot_standalone>` or
:ref:`With your ORM <depot_with_your_orm>`.

.. _depot_standalone:

Depot Standalone
-------------------------

Depot can easily be used to save and retrieve files in any python script,
Just get a depot using the :class:`depot.manager.DepotManager` and store the files.
With each file, additional data commonly used in HTTP is stored like *last_modified*,
*content_type* and so on. This data is available inside the :class:`depot.io.interfaces.StoredFile`
which is returned when getting the file back:

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


.. _depot_with_your_orm:

Attaching Files to Models
--------------------------

Depot also provides simple integration with SQLAlchemy for storing files attached
to your ORM document. Just declare them inside your models and assign the files:

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
=================

.. toctree::
   :maxdepth: 2

   userguide


API Reference
==================

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api
