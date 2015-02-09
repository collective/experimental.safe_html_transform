#!/usr/bin/python
##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Plone Foundation (http://plone.org/foundation/)
#
##########################################################

__authors__ = 'Anders Pearson <anders@columbia.edu>'
__docformat__ = 'restructuredtext'

import re

mapping = {138: 's', 140: 'OE', 142: 'z', 154: 's', 156: 'oe', 158: 'z', 159: 'Y',
192: 'A', 193: 'A', 194: 'A', 195: 'A', 196: 'A', 197: 'a', 198: 'E', 199: 'C',
200: 'E', 201: 'E', 202: 'E', 203: 'E', 204: 'I', 205: 'I', 206: 'I', 207: 'I',
208: 'D', 209: 'n', 211: 'O', 212: 'O', 214: 'O', 216: 'O', 217: 'U', 218: 'U',
219: 'U', 220: 'U', 221: 'y', 223: 'ss', 224: 'a', 225: 'a', 226: 'a', 227: 'a',
228: 'a', 229: 'a', 230: 'e', 231: 'c', 232: 'e', 233: 'e', 234: 'e', 235: 'e',
236: 'i', 237: 'i', 238: 'i', 239: 'i', 240: 'd', 241: 'n', 243: 'o', 244: 'o',
246: 'o', 248: 'o', 249: 'u', 250: 'u', 251: 'u', 252: 'u', 253: 'y', 255: 'y'}


def normalizeISO(text=""):
    fixed = []
    for c in list(text):
        if ord(c) < 256:
            c = mapping.get(ord(c),c)
        else:
            c = "%x" % ord(c)
        fixed.append(c)
    return "".join(fixed)


pattern1 = re.compile(r"^([^\.]+)\.(\w{,4})$")
pattern2 = re.compile(r'r"([\W\-]+)"')
def titleToNormalizedId(title=""):
    title = title.lower()
    title = title.strip()
    title = normalizeISO(title)
    base = title
    ext = ""
    m = pattern1.match(title)
    if m:
        base = m.groups()[0]
        ext = m.groups()[1]
    parts = pattern2.split(base)

    slug = re.sub(r"[\W\-]+","-",base)
    slug = re.sub(r"^\-+","",slug)
    slug = re.sub(r"\-+$","",slug)
    if ext != "":
        slug = slug + "." + ext
    return slug


tests = [
(u"This is a normal title.", "this-is-a-normal-title"),
(u"Short sentence. Big thoughts.", "short-sentence-big-thoughts"),
(u"Some298374NUMBER", "some298374number"),
(u'Eksempel \xe6\xf8\xe5 norsk \xc6\xd8\xc5', u'eksempel-aoa-norsk-aoa'),
(u'\u9ad8\u8054\u5408 Chinese', u'2837821-chinese'),
(u'\u30a2\u30ec\u30af\u30b5\u30f3\u30c0\u30fc\u3000\u30ea\u30df Japanese', u'23987643-japanese'),
(u'\uc774\ubbf8\uc9f1 Korean', u'987342-korean'),
(u'\u0e2d\u0e40\u0e25\u0e47\u0e01\u0e0b\u0e32\u0e19\u0e40\u0e14\u0e2d\u0e23\u0e4c \u0e25\u0e35\u0e21 Thai', u'7265837-thai'),
(u'About folder.gif', u'about-folder.gif')]

if __name__ == "__main__":
    import profile

    for original,correct in tests:
        sanitized = titleToNormalizedId(original)
        print sanitized


