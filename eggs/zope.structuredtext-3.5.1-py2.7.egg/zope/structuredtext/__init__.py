##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Zope structured text markeup

Consider the following example::

  >>> from zope.structuredtext.stng import structurize
  >>> from zope.structuredtext.document import DocumentWithImages
  >>> from zope.structuredtext.html import HTMLWithImages
  >>> from zope.structuredtext.docbook import DocBook

  We first need to structurize the string and make a full-blown
  document out of it:

  >>> struct = structurize(structured_string)
  >>> doc = DocumentWithImages()(struct)

  Now feed it to some output generator, in this case HTML or DocBook:
  
  >>> output = HTMLWithImages()(doc, level=1)
  >>> output = DocBook()(doc, level=1)

"""
__docformat__ = 'restructuredtext'

import re
from string import letters

from zope.structuredtext.stng import structurize
from zope.structuredtext.document import DocumentWithImages
from zope.structuredtext.html import HTMLWithImages

def stx2html(aStructuredString, level=1, header=1):
    st = structurize(aStructuredString)
    doc = DocumentWithImages()(st)
    return HTMLWithImages()(doc, header=header, level=level)

def stx2htmlWithReferences(text, level=1, header=1):
    text = re.sub(
        r'[\000\n]\.\. \[([0-9_%s-]+)\]' % letters,
        r'\n  <a name="\1">[\1]</a>',
        text)

    text = re.sub(
        r'([\000- ,])\[(?P<ref>[0-9_%s-]+)\]([\000- ,.:])' % letters,
        r'\1<a href="#\2">[\2]</a>\3',
        text)

    text = re.sub(
        r'([\000- ,])\[([^]]+)\.html\]([\000- ,.:])',
        r'\1<a href="\2.html">[\2]</a>\3',
        text)

    return stx2html(text, level=level, header=header)
