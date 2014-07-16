Depot with Database
=============================

Depot provides built-in support for attachments to models, uploading a file
and attaching it to a database entry is as simple as assigning the file itself
to a model field.

Attaching to Models
------------------------------

Attaching files to models is as simple as declaring a field on the model itself,
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

Most important property is probably the ``.url`` property which provides an URL where the
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

Custom Attachment Types
========================

Often attaching a file to the model is not enough, if a video is uploaded you probably
want to convert it to a supported format. Or if a big image is uploaded you might want
to scale it down.

Most simple changes can be achieved using **Filters**, filters can create thumbnails of
an image or trigger actions when the file gets uploaded, multiple filters can be specified
as a list inside the ``filters`` parameter of the column. More complex actions like
editing the content before it gets uploaded can be achieved subclassing
:class:`.UploadedFile` and passing it as column ``upload_type``.

Attachment Filters
------------------------------

File filters are created by subclassing :class:`.FileFilter` class, the only required
method to implement is :meth:`.FileFilter.on_save` which you are required implement with
the actions you want to perform. The method will receive the uploaded file (after it already
got uploaded) and can add properties to it.

Inside filters the original content is available as a property of the uploaded file, by
accessing ``original_content`` you can read the original content but not modify it, as
the file already got uploaded changing the original content has no effect.

If you need to store additional files, only use the :meth:`.UploadedFile.store_content`
method so that they are correctly tracked by the unit of work and deleted when the
associated document is deleted.

A filter that creates a thumbnail for an image would look like::

    from depot.io import utils
    from PIL import Image
    from io import BytesIO


    class WithThumbnailFilter(FileFilter):
        def __init__(self, size=(128,128), format='PNG'):
            self.thumbnail_size = size
            self.thumbnail_format = format

        def on_save(self, uploaded_file):
            content = utils.file_from_content(uploaded_file.original_content)

            thumbnail = Image.open(content)
            thumbnail.thumbnail(self.thumbnail_size, Image.BILINEAR)
            thumbnail = thumbnail.convert('RGBA')
            thumbnail.format = self.thumbnail_format

            output = BytesIO()
            thumbnail.save(output, self.thumbnail_format)
            output.seek(0)

            thumb_file_name = 'thumb.%s' % self.thumbnail_format.lower()
            thumb_path, thumb_id = uploaded_file.store_content(output, thumb_file_name)
            uploaded_file['thumb_id'] = thumb_id
            uploaded_file['thumb_path'] = thumb_path
            uploaded_file['thumb_url'] = DepotManager.get_middleware().url_for(thumb_path)

To use it, just provide the ``filters`` parameter in your :class:`.UploadedFileField`
or :class:`.UploadedFileProperty`::

    class Document(DeclarativeBase):
        __tablename__ = 'docu'

        uid = Column(Integer, autoincrement=True, primary_key=True)
        name = Column(Unicode(16), unique=True)
        photo = Column(UploadedFileField(filters=(WithThumbnailFilter((12, 12), 'PNG'),)))

As :class:`.UploadedFile` remembers every value/attribute stored before saving it on
the database, all the *thumb_id*, *thumb_path* and *thumb_url* values will be available
when loading back the document::

    >>> d = DBSession.query(Document).filter_by(name='Foo').first()
    >>> print d.thumb_url
    /depot/default/5b1a489e-0d33-11e4-8e2a-0800277ee230


Special Attachments
------------------------------


