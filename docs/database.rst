Depot with Database
=============================

Depot provides built-in support for attachments to models, uploading a file
and attaching it to a database entry is as simple as assigning the file itself
to a model field.

Attaching to Models
------------------------------

Attaching files to models is as simple as declaring a field of the model itself,
support is currently provided for **SQLAlchemy** through the
:class:`depot.fields.sqlalchemy.UploadedFileField` and for **Ming (MongoDB)** through
the :class:`depot.fields.ming.UploadedFileProperty`::

    from depot.fields.sqlalchemy import UploadedFileField

    class Document(Base):
        __tablename__ = 'document'

        uid = Column(Integer, autoincrement=True, primary_key=True)
        name = Column(Unicode(16), unique=True)

        content = Column(UploadedFileField)

To actually store the file into the Document, assigning it to the ``content`` property
is usually enough, just like files uploaded using :meth:`.FileStorage.create` both
file objects, ``cgi.FieldStorage`` and ``bytes`` can be used::

    # Store documents with attached files, the source can be a file or bytes
    doc = Document(name=u'Foo',
                   content=open('/tmp/document.xls'))
    DBSession.add(doc)

.. note::
    In case of Python3 make sure the file is open in byte mode.

Depot will upload files to the default storage, to change where files are uploaded
use :meth:`.DepotManager.set_default`.

Uploaded Files Information
------------------------------

Whenever a supported object is assigned to a :class:`.UploadedFileField` or
:class:`.UploadedFileProperty` it will be converted to a :class:`.UploadedFile` object.

This is the same object you will get back when reloading the models from database and
apart from the file itself which is accessible through the ``.file`` property, it provides
additional attributes described into the :class:`.UploadedFile` documentation itself.

Most important property is probably ``.url`` property which provides an URL where the
file can be accessed in case the storage supports HTTP or the :class:`.DepotMiddleware` is
available in your WSGI application.

Session Awareness
------------------------------

Whenever an object is *deleted* or a *rollback* is performed the files uploaded
during the unit of work or attached to the deleted objects are automatically deleted.

This is performed out of the box for SQLAlchemy, but requires the :class:`.DepotExtension`
to be registered as a session extension for Ming.

.. note::
    Ming doesn't currently provide an entry point for session clear, so files
    uploaded without a session flush won't be deleted when the session is removed.

Attachment Filters
------------------------------



Special Attachments
------------------------------


