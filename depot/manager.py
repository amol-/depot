import importlib

"""
- METTERE UN DIZIONARIO DI DEPOT {nome: depot}.
- ALLA CREAZIONE "from_config" VUOLE IL NOME DEL DEPOT.
- STORARE IN UNA VARIABILE QUALE E` IL DEFAULT_DEPOT (se il dizionario ha sol o1 chiave autodetectarlo)
COSI POI QUANDO SALVO UN FILE COME ATTACHMENT PUO` SALVARSI IL NOME DEL DEPOT DA CUI E` GESTITO
QUANDO CHIEDO URL DI UN FILE, SE LO STORAGE NON FORNISCE URL DI PER SE (S3) IL MIDDLEWARE PUO` CHIEDERE AL DEPOT GIUSTO IL FILE
"""

class DepotManager(object):
    """Takes care of creating the :class:`FileStoreage` in charge of managing application files.

    While this is used to create the default depot used by the application it can
    also create additional depots using the :meth:`new` method.

    """
    _default_depot = None
    _depots = {}

    @classmethod
    def set_default(cls, name):
        if name not in cls._depots:
            raise RuntimeError('%s depot has not been configured' % (name,))
        cls._default_depot = name

    @classmethod
    def get(cls, name=None):
        """Gets the application wide depot instance.

        Might return ``None`` if :meth:`configure` has not been
        called yet.

        """
        if name is None:
            name = cls._default_depot
        return cls._depots.get(name)

    @classmethod
    def configure(cls, name, config, prefix='depot.'):
        """Configures the application depot.

        This configures the application wide depot from a settings dictionary.
        The settings dictionary is usually loaded from an application configuration
        file where all the depot options are specified with a given ``prefix``.

        The default ``prefix`` is *depot.*, the minimum required setting
        is ``depot.backend`` which specified the required backend for files storage.
        Additional options depend on the choosen backend.

        """
        if name in cls._depots:
            raise RuntimeError('Depot %s has already been configured' % (name,))

        if cls._default_depot is None:
            cls._default_depot = name

        full_prefix = '%s.%s' % (prefix, name)
        cls._depots[name] = cls.from_config(config, full_prefix)
        return cls._depots[name]

    @classmethod
    def new(cls, backend, **options):
        module, classname = backend.rsplit('.', 1)
        backend = importlib.import_module(module)
        class_ = getattr(backend, classname)
        return class_(**options)

    @classmethod
    def from_config(cls, config, prefix='depot.'):
        """Creates a new depot from a settings dictionary.

        Behaves like the :meth:`configure` method but instead of configuring the application
        depot it creates a new one each time.
        """
        config = config or {}

        # Get preferred storage backend
        backend = config.get(prefix + 'backend', 'depot.io.local.LocalFileStorage')

        # Get all options
        prefixlen = len(prefix)
        options = dict((k[prefixlen:], config[k]) for k in config.keys() if k.startswith(prefix))
        options.pop(prefix+'backend', None)

        return cls.new(backend, **options)


get_depot = DepotManager.get
configure = DepotManager.configure
set_default = DepotManager.set_default