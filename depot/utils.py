from ._compat import percent_encode, unicode_text

try:
    from anyascii import anyascii
except ImportError:
    # Python2 doesn't support anyascii
    import unicodedata
    def anyascii(text):
        if not isinstance(text, unicode_text):
            text = text.decode("utf-8")
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore") or "unknown"


def make_content_disposition(disposition, fname):
    rfc6266_part = "filename*=utf-8''%s" % (percent_encode(fname, safe='!#$&+-.^_`|~', encoding='utf-8'), )
    ascii_part = 'filename="%s"' % (anyascii(fname), )
    return ';'.join((disposition, ascii_part, rfc6266_part))
