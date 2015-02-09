##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""Clipboard tests
"""
import unittest

import zope.component
from zope.annotation.interfaces import IAnnotations
from zope.component.testing import PlacelessSetup
from zope.principalannotation.utility import PrincipalAnnotationUtility
from zope.principalannotation.interfaces import IPrincipalAnnotationUtility

from zope.copypastemove import PrincipalClipboard
from zope.copypastemove.interfaces import IPrincipalClipboard


class PrincipalStub(object):

    def __init__(self, id):
        self.id = id


class PrincipalClipboardTest(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerAdapter(PrincipalClipboard, (IAnnotations, ),
                            IPrincipalClipboard)
        gsm.registerUtility(PrincipalAnnotationUtility(),
                            IPrincipalAnnotationUtility)

    def testAddItems(self):
        user = PrincipalStub('srichter')

        annotationutil = zope.component.getUtility(IPrincipalAnnotationUtility)
        annotations = annotationutil.getAnnotations(user)
        clipboard = IPrincipalClipboard(annotations)
        clipboard.addItems('move', ['bla', 'bla/foo', 'bla/bar'])
        expected = ({'action':'move', 'target':'bla'},
                    {'action':'move', 'target':'bla/foo'},
                    {'action':'move', 'target':'bla/bar'})

        self.failUnless(clipboard.getContents() == expected)
        clipboard.addItems('copy', ['bla'])
        expected = expected + ({'action':'copy', 'target':'bla'},)
        self.failUnless(clipboard.getContents() == expected)

    def testSetContents(self):
        user = PrincipalStub('srichter')

        annotationutil = zope.component.getUtility(IPrincipalAnnotationUtility)
        annotations = annotationutil.getAnnotations(user)
        clipboard = IPrincipalClipboard(annotations)

        expected = ({'action':'move', 'target':'bla'},
                    {'action':'move', 'target':'bla/foo'},
                    {'action':'move', 'target':'bla/bar'})
        clipboard.setContents(expected)
        self.failUnless(clipboard.getContents() == expected)
        clipboard.addItems('copy', ['bla'])
        expected = expected + ({'action':'copy', 'target':'bla'},)
        self.failUnless(clipboard.getContents() == expected)

    def testClearContents(self):
        user = PrincipalStub('srichter')

        annotationutil = zope.component.getUtility(IPrincipalAnnotationUtility)
        annotations = annotationutil.getAnnotations(user)
        clipboard = IPrincipalClipboard(annotations)
        clipboard.clearContents()
        self.failUnless(clipboard.getContents() == ())

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(PrincipalClipboardTest),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

