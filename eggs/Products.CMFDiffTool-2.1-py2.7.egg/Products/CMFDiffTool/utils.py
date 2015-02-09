# -*- coding: utf-8 -*-
def safe_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        value = unicode(value)
    except UnicodeDecodeError:
        value = value.decode('utf-8', 'replace')
    return value

def safe_utf8(value):
    return safe_unicode(value).encode('utf-8')
