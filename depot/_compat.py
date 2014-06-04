import platform, sys

if platform.system() == 'Windows':  # pragma: no cover
    WIN = True
else:
    WIN = False

# True if we are running on Python 2.
PY2 = sys.version_info[0] == 2


if not PY2:  # pragma: no cover
    string_type = str
    unicode_text = str
    byte_string = bytes
else:  # pragma: no cover
    string_type = basestring
    unicode_text = unicode
    byte_string = str


def with_metaclass(meta, base=object):
    """Create a base class with a metaclass."""
    return meta("NewBase", (base,), {})