##############################################################################
#
# Copyright (c) 2004-2009 Zope Foundation and Contributors.
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
"""Doc tests for the pagetemplate's 'engine' module
"""
import unittest

class DummyNamespace(object):

    def __init__(self, context):
        self.context = context

class EngineTests(unittest.TestCase):

    def setUp(self):
        from zope.component.testing import setUp
        setUp()

    def tearDown(self):
        from zope.component.testing import tearDown
        tearDown()

    def test_function_namespaces_return_secured_proxies(self):
        # See https://bugs.launchpad.net/zope3/+bug/98323
        from zope.component import provideAdapter
        from zope.traversing.interfaces import IPathAdapter
        from zope.pagetemplate.engine import _Engine
        from zope.proxy import isProxy
        provideAdapter(DummyNamespace, (None,), IPathAdapter, name='test')
        engine = _Engine()
        namespace = engine.getFunctionNamespace('test')
        self.failUnless(isProxy(namespace))

class DummyEngine(object):

    def getTypes(self):
        return {}

class DummyContext(object):

    _engine = DummyEngine()

    def __init__(self, **kw):
        self.vars = kw

class ZopePythonExprTests(unittest.TestCase):

    def test_simple(self):
        from zope.pagetemplate.engine import ZopePythonExpr
        expr = ZopePythonExpr('python', 'max(a,b)', DummyEngine())
        self.assertEqual(expr(DummyContext(a=1, b=2)), 2)

    def test_allowed_module_name(self):
        from zope.pagetemplate.engine import ZopePythonExpr
        expr = ZopePythonExpr('python', '__import__("sys").__name__',
                              DummyEngine())
        self.assertEqual(expr(DummyContext()), 'sys')

    def test_forbidden_module_name(self):
        from zope.pagetemplate.engine import ZopePythonExpr
        from zope.security.interfaces import Forbidden
        expr = ZopePythonExpr('python', '__import__("sys").exit',
                              DummyEngine())
        self.assertRaises(Forbidden, expr, DummyContext())

    def test_disallowed_builtin(self):
        from zope.pagetemplate.engine import ZopePythonExpr
        expr = ZopePythonExpr('python', 'open("x", "w")', DummyEngine())
        self.assertRaises(NameError, expr, DummyContext())


def test_suite():
    from doctest import DocTestSuite
    suite = unittest.TestSuite()
    suite.addTest(DocTestSuite('zope.pagetemplate.engine'))
    suite.addTest(unittest.makeSuite(EngineTests))
    suite.addTest(unittest.makeSuite(ZopePythonExprTests))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
