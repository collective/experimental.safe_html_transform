##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""Unit test logic for setting up and tearing down basic infrastructure
"""
import zope.component
from zope.publisher.browser import BrowserLanguages
from zope.publisher.http import HTTPCharsets

def setUp(test=None):
    zope.component.provideAdapter(HTTPCharsets)
    zope.component.provideAdapter(BrowserLanguages)

class PlacelessSetup(object):

    def setUp(self):
        setUp()
