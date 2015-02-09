##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Page Template based Resources Test

$Id: tests.py 103139 2009-08-24 11:58:22Z nadako $
"""
import os
import tempfile
import unittest

from zope.component import provideAdapter
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces import NotFound
from zope.security.checker import NamesChecker
from zope.testing import cleanup
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.interfaces import ITraversable

from zope.ptresource.ptresource import PageTemplateResourceFactory


checker = NamesChecker(('__call__', 'request', 'publishTraverse'))


class Test(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        provideAdapter(DefaultTraversable, (None,), ITraversable)

    def createTestFile(self, contents):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        open(path, 'w').write(contents)
        return path

    def testNoTraversal(self):
        path = self.createTestFile('<html><body><p>test</p></body></html>')
        request = TestRequest()
        factory = PageTemplateResourceFactory(path, checker, 'test.pt')
        resource = factory(request)
        self.assertRaises(NotFound, resource.publishTraverse,
                          resource.request, ())
        os.unlink(path)

    def testBrowserDefault(self):
        path = self.createTestFile(
            '<html><body tal:content="request/test_data"></body></html>')
        test_data = "Foobar"
        request = TestRequest(test_data=test_data)
        factory = PageTemplateResourceFactory(path, checker, 'testresource.pt')
        resource = factory(request)
        view, next = resource.browserDefault(request)
        self.assertEquals(view(),
                          '<html><body>%s</body></html>' % test_data)
        self.assertEquals('text/html',
                          request.response.getHeader('Content-Type'))
        self.assertEquals(next, ())

        request = TestRequest(test_data=test_data, REQUEST_METHOD='HEAD')
        resource = factory(request)
        view, next = resource.browserDefault(request)
        self.assertEquals(view(), '')
        self.assertEquals('text/html',
                          request.response.getHeader('Content-Type'))
        self.assertEquals(next, ())
        
        os.unlink(path)


def test_suite():
    return unittest.makeSuite(Test)
