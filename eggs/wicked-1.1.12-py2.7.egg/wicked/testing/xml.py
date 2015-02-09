import re

_strip_left = re.compile(r">\s*", re.MULTILINE)
_strip_right = re.compile(r"\s*<", re.MULTILINE)

def xstrip(text):
    """Simplistic xml space normalizer.
    """
    if not text:
        return ''
    text, num = _strip_left.subn(">", text)
    text, num = _strip_right.subn("<", text)
    return text
