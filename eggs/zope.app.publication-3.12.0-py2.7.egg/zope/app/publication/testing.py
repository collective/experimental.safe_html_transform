##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""zope.app.publication common test related classes/functions/objects.

$Id: testing.py 110812 2010-04-13 16:30:31Z thefunny42 $
"""

__docformat__ = "reStructuredText"

from zope.app.wsgi.testlayer import BrowserLayer
from zope.publisher.browser import BrowserPage
import zope.app.publication


class DefaultTestView(BrowserPage):

    def __call__(self):
        self.request.response.setHeader(
            'Content-Type', 'text/html;charset=utf-8')
        return "<html><body>Test</body></html>"


PublicationLayer = BrowserLayer(zope.app.publication, name='PublicationLayer')

