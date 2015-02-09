##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os, sys

# Load fixture
from Testing import ZopeTestCase

# Install our product
ZopeTestCase.installProduct('ExternalEditor')

from OFS.SimpleItem import SimpleItem
class SideEffects(SimpleItem):
    meta_type = 'Side Effects'
    def __init__(self, id, content):
        self.id = id
        self.content = content
    def manage_FTPget(self, REQUEST, RESPONSE):
        RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.content

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    files = [
        'link.txt',
        'edit.txt',
        ]
    for f in files:
        suite.addTest(
            FileSuite(f, package='Products.ExternalEditor.tests'))
    return suite
