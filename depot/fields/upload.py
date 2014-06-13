from depot.manager import DepotManager
import json


class UploadedFile(dict):
    """A dictionary that provides attribute-style access."""
    def __init__(self, content, depot_name=None):
        super(UploadedFile, self).__init__()

        if isinstance(content, dict):
            self.update(content)
        else:
            if depot_name is None:
                depot_name = DepotManager.get_default()

            self['depot_name'] = depot_name
            self.process_content(content)

    def process_content(self, content):
        d = self.depot
        f = d.create(content)

        self['file_id'] = f
        self['path'] = '%s/%s' % (self.depot_name, f)

    def encode(self):
        return json.dumps(self)

    @classmethod
    def decode(cls, data):
        return cls(json.loads(data))

    @property
    def depot(self):
        return DepotManager.get(self.depot_name)

    @property
    def file(self):
        return self.depot.get(self.file_id)

    def __getitem__(self, key):
        return  dict.__getitem__(self, key)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    __setattr__ = dict.__setitem__

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)
