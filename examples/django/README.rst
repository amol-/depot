Setting Up DEPOT on Django
==========================

Setup a **Storage** where files can be saved
--------------------------------------------

Make sure you provide a storage to save files using ``DepotManager``
in ``wsgi.py``, the following example configures a local
files storage named ``default``::

    from django.conf import settings
    from depot.manager import DepotManager
    DepotManager.configure('default', settings.DEPOT, prefix='')

The ``default`` storage is configured from settings provided in
``settings.py`` through ``DEPOT`` key. In this case we set it up
to save files on local disk on ``/tmp``::

    DEPOT = {
        'storage_path': '/tmp/'
    }

Register a DEPOT middleware to serve files
------------------------------------------

Once a storage is configuredd we can use ``DepotManager`` to
wrap our application with the depot middleware which will
serve the saved files on ``/depot`` url. This is still
done in ``wsgi.py``::

    from depot.manager import DepotManager
    application = DepotManager.make_middleware(application)

Start uploading your files!
---------------------------

Files you upload using ``DepotManager.get().create(file)``
can be retrieved back on ``/depot/default/FILEID`` url where
``fileid`` is returned by the ``create()`` method.
