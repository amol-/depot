Setting Up DEPOT on TurboGears
==============================

Setup a **Storage** where files can be saved
--------------------------------------------

Inside ``config/app_cfg.py`` use ``DepotManager`` to
configure a storage to save files, the following example configures a local
files storage named ``default`` that saves files on ``/tmp``::

    from depot.manager import DepotManager
    DepotManager.configure('default', {'depot.storage_path': '/tmp/'})


Register a DEPOT middleware to serve files
------------------------------------------

Inside ``config/middleware.py`` use ``DepotManager`` to
wrap your turbogears application with the depot middleware which will
serve the saved files on ``/depot`` url::

    from depot.manager import DepotManager
    app = DepotManager.make_middleware(app)

Start uploading your files!
---------------------------

Files you upload using ``DepotManager.get().create(file)``
can be retrieved back on ``/depot/default/FILEID`` url where
``fileid`` is returned by the ``create()`` method.


TurboGears Example Installation
===============================

Install ``depotexample`` using the setup.py script::

    $ cd depotexample
    $ python setup.py develop

Create the project database for any model classes defined::

    $ gearbox setup-app

Start the http server::

    $ gearbox serve --reload --debug
