##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Tests of PublicationTraverser
"""
from unittest import TestCase, main, makeSuite
from zope.testing.cleanup import CleanUp
from zope.component import provideAdapter
from zope.interface import Interface, implements
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.security.proxy import removeSecurityProxy
from zope.traversing.interfaces import ITraversable

class TestPublicationTraverser(CleanUp, TestCase):

    def testViewNotFound(self):
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        self.assertRaises(NotFound, t.traverseName, request, ob, '@@foo')

    def testViewFound(self):
        provideAdapter(DummyViewTraverser, (Interface, Interface),
            ITraversable, name='view')
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        proxy = t.traverseName(request, ob, '@@foo')
        view = removeSecurityProxy(proxy)
        self.assertTrue(proxy is not view)
        self.assertEqual(view.__class__, View)
        self.assertEqual(view.name, 'foo')

    def testDot(self):
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        self.assertEqual(ob, t.traverseName(request, ob, '.'))

    def testNameNotFound(self):
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        self.assertRaises(NotFound, t.traverseName, request, ob, 'foo')

    def testNameFound(self):
        provideAdapter(DummyPublishTraverse, (Interface, Interface),
            IPublishTraverse)
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        proxy = t.traverseName(request, ob, 'foo')
        view = removeSecurityProxy(proxy)
        self.assertTrue(proxy is not view)
        self.assertEqual(view.__class__, View)
        self.assertEqual(view.name, 'foo')

    def testDirectTraversal(self):
        request = TestRequest()
        ob = DummyPublishTraverse(Content(), request)
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        proxy = t.traverseName(request, ob, 'foo')
        view = removeSecurityProxy(proxy)
        self.assertTrue(proxy is not view)
        self.assertEqual(view.__class__, View)
        self.assertEqual(view.name, 'foo')

    def testPathNotFound(self):
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        self.assertRaises(NotFound, t.traversePath, request, ob, 'foo/bar')

    def testPathFound(self):
        provideAdapter(DummyPublishTraverse, (Interface, Interface),
            IPublishTraverse)
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        proxy = t.traversePath(request, ob, 'foo/bar')
        view = removeSecurityProxy(proxy)
        self.assertTrue(proxy is not view)
        self.assertEqual(view.__class__, View)
        self.assertEqual(view.name, 'bar')

    def testComplexPath(self):
        provideAdapter(DummyPublishTraverse, (Interface, Interface),
            IPublishTraverse)
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        proxy = t.traversePath(request, ob, 'foo/../alpha//beta/./bar')
        view = removeSecurityProxy(proxy)
        self.assertTrue(proxy is not view)
        self.assertEqual(view.__class__, View)
        self.assertEqual(view.name, 'bar')

    def testTraverseRelativeURL(self):
        provideAdapter(DummyPublishTraverse, (Interface, Interface),
            IPublishTraverse)
        provideAdapter(DummyBrowserPublisher, (Interface,),
            IBrowserPublisher)
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        proxy = t.traverseRelativeURL(request, ob, 'foo/bar')
        view = removeSecurityProxy(proxy)
        self.assertTrue(proxy is not view)
        self.assertEqual(view.__class__, View)
        self.assertEqual(view.name, 'more')

    def testMissingSkin(self):
        ob = Content()
        from zope.traversing.publicationtraverse import PublicationTraverser
        t = PublicationTraverser()
        request = TestRequest()
        self.assertRaises(
            NotFound, t.traversePath, request, ob, '/++skin++missingskin')


class IContent(Interface):
    pass

class Content(object):
    implements(IContent)

class View(object):
    def __init__(self, name):
        self.name = name

class DummyViewTraverser(object):
    implements(ITraversable)

    def __init__(self, content, request):
        self.content = content

    def traverse(self, name, furtherPath):
        return View(name)

class DummyPublishTraverse(object):
    implements(IPublishTraverse)

    def __init__(self, context, request):
        pass

    def publishTraverse(self, request, name):
        return View(name)

class DummyBrowserPublisher(object):
    implements(IBrowserPublisher)

    def __init__(self, context):
        self.context = removeSecurityProxy(context)

    def browserDefault(self, request):
        if self.context.name != 'more':
            return self.context, ['more']
        else:
            return self.context, ()


def test_suite():
    return makeSuite(TestPublicationTraverser)

if __name__ == '__main__':
    main()
