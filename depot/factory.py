import importlib


class DepotFactory(object):
    """Takes care of creating the :class:`FileStoreage` in charge of managing application files.

    While this is used to create the default depot used by the application it can
    also create additional depots using the :meth:`new` method.

    """
    _depot = None

    @classmethod
    def get(cls):
        """Gets the application wide depot instance.

        Might return ``None`` if :meth:`configure` has not been
        called yet.

        """
        return cls._depot

    @classmethod
    def configure(cls, config, prefix='depot.'):
        """Configures the application depot.

        This configures the application wide depot from a settings dictionary.
        The settings dictionary is usually loaded from an application configuration
        file where all the depot options are specified with a given ``prefix``.

        The default ``prefix`` is *depot.*, the minimum required setting
        is ``depot.backend`` which specified the required backend for files storage.
        Additional options depend on the choosen backend.

        """
        if cls._depot is not None:
            raise RuntimeError('Depot has already been configured')

        cls._depot = cls.from_config(config, prefix)
        return cls._depot

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


get_depot = DepotFactory.get
configure = DepotFactory.configure