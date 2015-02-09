##############################################################################
#
# Copyright (c) 2001-2009 Zope Foundation and Contributors.
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
"""Simple View Class Tests

$Id: test_simpleviewclass.py 111996 2010-05-05 17:34:04Z tseaver $
"""
import unittest

class Test_SimpleTestView(unittest.TestCase):

    def _getTargetClass(self):
        from zope.browserpage.tests.simpletestview import SimpleTestView
        return SimpleTestView

    def _makeOne(self, context, request):
        return self._getTargetClass()(context, request)

    def test_simple(self):
        from zope.publisher.browser import TestRequest
        context = DummyContext()
        request = TestRequest()
        view = self._makeOne(context, request)
        macro = view['test']
        out = view()
        self.assertEqual(out,
                         '<html>\n'
                         '  <body>\n'
                         '    <p>hello world</p>\n'
                         '  </body>\n</html>\n')

class Test_SimpleViewClass(unittest.TestCase):

    def _getTargetClass(self):
        from zope.browserpage.simpleviewclass import SimpleViewClass
        return SimpleViewClass

    def _makeKlass(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test___name__(self):
        klass = self._makeKlass('testsimpleviewclass.pt', name='test.html')
        view = klass(None, None)
        self.assertEqual(view.__name__, 'test.html')

    def test___getitem___(self):
        klass = self._makeKlass('testsimpleviewclass.pt', name='test.html')
        view = klass(None, None)
        self.assert_(view['test'] is not None)
        self.assertRaises(KeyError, view.__getitem__, 'foo')

    def test_w_base_classes(self):
        from zope.publisher.browser import TestRequest
        class BaseClass(object):
            pass

        klass = self._makeKlass('testsimpleviewclass.pt', bases=(BaseClass, ))

        self.failUnless(issubclass(klass, BaseClass))

        ob = DummyContext()
        request = TestRequest()
        view = klass(ob, request)
        macro = view['test']
        out = view()
        self.assertEqual(out,
                         '<html>\n'
                         '  <body>\n'
                         '    <p>hello world</p>\n'
                         '  </body>\n</html>\n')

class Test_simple(unittest.TestCase):

    def _getTargetClass(self):
        from zope.browserpage.simpleviewclass import simple
        return simple

    def _makeOne(self, context=None, request=None):
        if context is None:
            context = DummyContext()
        if request is None:
            request = DummyRequest()
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IBrowserPublisher(self):
        from zope.interface.verify import verifyClass
        from zope.publisher.interfaces.browser import IBrowserPublisher
        verifyClass(IBrowserPublisher, self._getTargetClass())

    def test_browserDefault(self):
        request = DummyRequest()
        view = self._makeOne(request=request)
        self.assertEqual(view.browserDefault(request), (view, ()))

    def test_publishTraverse_not_index_raises_NotFound(self):
        from zope.publisher.interfaces import NotFound
        request = DummyRequest()
        view = self._makeOne(request=request)
        self.assertRaises(NotFound, view.publishTraverse, request, 'nonesuch')

    def test_publishTraverse_w_index_returns_index(self):
        request = DummyRequest()
        view = self._makeOne(request=request)
        index = view.index = DummyTemplate()
        self.failUnless(view.publishTraverse(request, 'index.html') is index)

    def test___getitem___uses_index_macros(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        index.macros = {}
        index.macros['aaa'] = aaa = object()
        self.failUnless(view['aaa'] is aaa)

    def test___call___no_args_no_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view()
        self.failUnless(result is index)
        self.assertEqual(index._called_with, ((), {}))

    def test___call___w_args_no_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view('abc')
        self.failUnless(result is index)
        self.assertEqual(index._called_with, (('abc',), {}))

    def test___call___no_args_w_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view(foo='bar')
        self.failUnless(result is index)
        self.assertEqual(index._called_with, ((), {'foo': 'bar'}))

    def test___call___no_args_no_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view('abc', foo='bar')
        self.failUnless(result is index)
        self.assertEqual(index._called_with, (('abc',), {'foo': 'bar'}))


class DummyContext:
    pass

class DummyResponse:
    pass

class DummyRequest:
    debug = False
    response = DummyResponse()

class DummyTemplate:
    def __call__(self, *args, **kw):
        self._called_with = (args, kw)
        return self

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test_SimpleTestView),
        unittest.makeSuite(Test_SimpleViewClass),
        unittest.makeSuite(Test_simple),
    ))
