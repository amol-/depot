from datetime import datetime, timezone
from urllib.parse import quote

from anyascii import anyascii


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utcfromtimestamp_naive(ts):
    return datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None)


def make_content_disposition(disposition, fname):
    rfc6266_part = "filename*=utf-8''%s" % (quote(fname, safe='!#$&+-.^_`|~', encoding='utf-8', errors='strict'), )
    ascii_part = 'filename="%s"' % (anyascii(fname), )
    return ';'.join((disposition, ascii_part, rfc6266_part))
