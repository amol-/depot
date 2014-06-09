import json


class FileInfo(dict):
    """A dictionary that provides attribute-style access."""
    def __init__(self, data=None):
        if data is not None:
            data = json.loads(data)
        super(FileInfo, self).__init__(data)

    @classmethod
    def marshall(cls, data):
        return json.dumps(data)

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
