from ._compat import percent_encode

try:
    from unidecode import unidecode as fix_chars
except ImportError:
    import sys
    from unicodedata import normalize
    if (sys.version_info > (3, 0)):
        from urllib.parse import quote
    else:
        from urllib import quote
    def fix_chars(string):
        return quote(normalize('NFKC', string))

def make_content_disposition(disposition, fname):
    rfc6266_part = "filename*=utf-8''%s" % (percent_encode(fname, safe='!#$&+-.^_`|~', encoding='utf-8'), )
    ascii_part = 'filename="%s"' % (fix_chars(fname), )
    return ';'.join((disposition, ascii_part, rfc6266_part))
