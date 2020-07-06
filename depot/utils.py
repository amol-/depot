try:
    from unidecode import unidecode as fix_chars
except:
    from unicodedata import normalize
    def fix_chars(str):
        normalize('NFKC', str).encode('ascii','ignore').decode('ascii')
from ._compat import percent_encode


def make_content_disposition(disposition, fname):
    rfc6266_part = "filename*=utf-8''%s" % (percent_encode(fname, safe='!#$&+-.^_`|~', encoding='utf-8'), )
    ascii_part = 'filename="%s"' % (fix_chars(fname), )
    return ';'.join((disposition, ascii_part, rfc6266_part))
