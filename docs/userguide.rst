Getting Started with Depot
==============================

Configuring DepotManager
------------------------------

The DepotManager is the entity in charge of configuring and handling file storages inside your
application. To start saving files the first required step is to configure a file storage through
the DepotManager.

This can be done using :meth:`.DepotManager.configure` which accepts a storage name (used
to identify the storage in case of multiple storages) and a set of configuration options::

    DepotManager.configure('default', {
        'depot.storage_path': './files'
    })

By default a :class:`depot.io.local.LocalFileStorage` storage is configured, LocalFileStorage
saves files on the disk at the ``storage_path``. You can use one of the available
storages through the ``.backend`` option. To store data on GridFS you would use::

    DepotManager.configure('my_gridfs', {
        'depot.backend': 'depot.io.gridfs.GridFSStorage',
        'depot.mongouri': 'mongodb://localhost/db'
    })

every other option apart the ``.backend`` one will be passed to the storage as
a constructor argument. You can even use your own storage by setting the full python
path of the class you want to use.

By default the first configured storage is the default one, which will be used whenever
no explict storage is specified, to change the default storage you can use
:meth:`.DepotManager.set_default` with the name of the storage you want to make the
default one.

Getting a Storage
------------------------------

Once you have configured at least one storage, you can get it back using the
:meth:`.DepotManager.get` method. If you pass a specific storage name it will retrieve
the storage configured for that name::

    depot = DepotManager.get('my_gridfs')

Otherwise the default storage can be retrieved by omitting the name argument::

    depot = DepotManager.get()

Save and Manage Files
=============================

Saving and Retrieving Files
------------------------------

Once you have a working storage, saving files is as easy as calling the :meth:`.FileStorage.create`
method passing the file (or the ``bytes``) you want to store::

    depot = DepotManager.get()
    fileid = depot.create(open('/tmp/file.png'))

The returned ``fileid`` will be necessary when you want to get back the stored file.
By default the ``name``, ``content_type`` and all the properties available through the
:class:`.StoredFile` object are automatically detect from the argument file object.

If you want to explicitly set filename and content type they can be passed as arguments
to the ``create`` method::

    fileid = depot.create(open('/tmp/file.png'), 'thumbnail.png', 'image/png')

Getting the file back can be done using :meth:`.FileStorage.get` from the storage itself::

    stored_file = depot.get(fileid)

Getting back the file will only retrieve the file metadata and will return an :class:`.StoredFile`
object, if you actually want to read the file content you should then call the ``read`` method::

    stored_file.content_type  # This will be 'image/png'
    image = stored_file.read()

If you don't have the depot instance available, you can use the :meth:`.DepotManager.get_file`
method which takes the path of the stored file. Paths are in the form ``depot_name/fileid``::

    stored_file = DepotManager.get_file('my_gridfs/%s' % fileid)

Replacing and Deleting Files
------------------------------

If you don't need a file anymore it can easily be deleted using the :meth:`.FileStorage.delete`
method with the file id::

    depot.delete(fileid)

The ``delete`` method is guaranteed to be idempotent, so calling it multiple times will
not lead to errors.

The storage can also be used to replace existing files, replacing the content of a file will
actually also replace the file metadata::

    depot.replace(fileid, open('/tmp/another_image.jpg'), 'thumbnail.jpg', 'image/png')

This has the same behavior of deleting the old file and storing a new one, but instead of
generating a new id it will reuse the existing one. As for the ``create`` call the filename
and content type arguments can be omitted and will be detected from the file itself when
available.

Depot for the Web
=============================

Files Metadata
------------------------------

As Depot has been explicitly designed for web applications development, it will provide
all the file metadata which is required for HTTP Headers when serving files or which is common
in the web world.

This is provided by the :class:`.StoredFile` you retrieve from the file storage and includes:

    * filename -> Original name of the file, if you need to serve it to the user for download.
    * content_type -> File content type, for the response content type when serving file back
      the file to the browser.
    * last_modified -> Can be used to implement caching and last modified header in HTTP.
    * content_length -> Size of the file, is usually the content length of the HTTP response when
      serving the file back.

Serving Files on HTTP
------------------------------

In case of storages that directly support serving files on HTTP
(like :class:`depot.io.awss3.S3Storage`) the stored file itself can be retrieved at the url
provided by :class:`.StoredFile.public_url`. In case the ``public_url`` is ``None`` it means
that the storage doesn't provide HTTP access directly.

In such case files can be served using a :class:`.DepotMiddleware` WSGI middleware. The
DepotMiddlware supports serving files from any backend, support ETag caching and in case of
storages directly supporting HTTP it will just redirect the user to the storage itself.

Unless you need to achieve maximum performances it is usually a good approach to just use
the WSGI Middleware and let it serve all your files for you::

    app = DepotManager.make_middleware(app)

By default the Depot middleware will serve the files at the ``/depot`` URL using their path
(same passed to the :meth:`.DepotManager.get_file` method). So in case you need to retrieve
a file with id **3774a1a0-0879-11e4-b658-0800277ee230** stored into **my_gridfs** depot the
URL will be ``/depot/my_gridfs/3774a1a0-0879-11e4-b658-0800277ee230``.

Changing base URL and caching can be done through the :meth:`.DepotManager.make_middleware`
options, any option passed to ``make_middlware`` will be forwarded to :class:`.DepotMiddleware`.


Handling Multiple Storages
==============================

Using Multiple Storages
------------------------------

Multiple storages can be used inside the same application, most common operations require
the storage itself or the full file path, so you can use multiple storages without risk
of collisions.

To start using multiple storages just call the :meth:`.DepotManager.configure` multiple times
and give each storage a unique name. You will be able to retrieve the correct storage by name.

Switching Default Storage
------------------------------

Once you started uploading files to a storage, it is best to avoid configuring another
storage to the same name. Doing that will probably break all the previously uploaded files
and will cause confusion.

If you want to switch to a different storage for saving your files just configure two
storages giving the new storage an unique name and switch the default storage using
the :meth:`.DepotManager.set_default` function.
