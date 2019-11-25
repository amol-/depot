import platform, sys


if platform.system() == 'Windows':  # pragma: no cover
    WIN = True
else:
    WIN = False

# True if we are running on Python 2.
PY2 = sys.version_info[0] == 2


if not PY2:  # pragma: no cover
    from urllib.parse import quote, unquote

    string_type = str
    unicode_text = str
    byte_string = bytes
    wsgi_string = str

    def u_(s):
        return str(s)

    def bytes_(s):
        return str(s).encode('ascii', 'strict')

    def percent_encode(string, safe, encoding):
        return quote(string, safe, encoding, errors='strict')

    def percent_decode(string):
        return unquote(string)

else:  # pragma: no cover
    from urllib import quote, unquote

    string_type = basestring
    unicode_text = unicode
    byte_string = str
    wsgi_string = str

    def u_(s):
        return unicode(s, 'utf-8')

    def bytes_(s):
        return str(s)

    def percent_encode(string, **kwargs):
        encoding = kwargs.pop('encoding')
        return quote(string.encode(encoding), **kwargs)

    def percent_decode(string):
        return unquote(string)


def with_metaclass(meta, base=object):
    """Create a base class with a metaclass."""
    return meta("NewBase", (base,), {})
