Setting Up DEPOT on Flask
=========================

Setup a **Storage** where files can be saved
--------------------------------------------

Make sure you provide a storage to save files using ``DepotManager``
in any place when your application starts, the following example configures a local
files storage named ``default`` that saves files on ``/tmp``::

    from depot.manager import DepotManager
    DepotManager.configure('default', {'depot.storage_path': '/tmp/'})


Register a DEPOT middleware to serve files
------------------------------------------

As soon as your Flask application is availalbe use ``DepotManager`` to
wrap it with the depot middleware which will
serve the saved files on ``/depot`` url::

    from depot.manager import DepotManager
    app.wsgi_app = DepotManager.make_middleware(app.wsgi_app)

Start uploading your files!
---------------------------

Files you upload using ``DepotManager.get().create(file)``
can be retrieved back on ``/depot/default/FILEID`` url where
``fileid`` is returned by the ``create()`` method.
