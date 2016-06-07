from unidecode import unidecode
from ._compat import percent_encode


def make_content_disposition(disposition, fname):
    rfc6266_part = "filename*=utf-8''%s" % (percent_encode(fname, safe='!#$&+-.^_`|~', encoding='utf-8'), )
    ascii_part = "filename=%s" % (unidecode(fname), )
    return ';'.join((disposition, ascii_part, rfc6266_part))
