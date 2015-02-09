# -*- coding: utf-8 -*-
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
"""Default TALES expression implementations tests.

$Id: test_expressions.py 126816 2012-06-11 19:00:21Z tseaver $
"""
import unittest

from zope.tales.engine import Engine
from zope.tales.interfaces import ITALESFunctionNamespace
from zope.tales.tales import Undefined
from zope.interface import implements

class Data(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self): return self.name

    __str__ = __repr__

class ErrorGenerator:

    def __getitem__(self, name):
        import __builtin__
        if name == 'Undefined':
            e = Undefined
        else:
            e = getattr(__builtin__, name, None)
        if e is None:
            e = SystemError
        raise e('mess')

class ExpressionTestBase(unittest.TestCase):

    def setUp(self):
        # Test expression compilation
        d = Data(
                 name = 'xander',
                 y = Data(
                    name = 'yikes',
                    z = Data(name = 'zope')
                    )
                 )
        at = Data(
                  name = 'yikes',
                  _d = d
                 )
        self.context = Data(
            vars = dict(
              x = d,
              y = Data(z = 3),
              b = 'boot',
              B = 2,
              adapterTest = at,
              dynamic = 'z',
              eightBits = 'déjà vu',
              ErrorGenerator = ErrorGenerator(),
              )
            )

        self.engine = Engine


class ExpressionTests(ExpressionTestBase):        

    def testSimple(self):
        expr = self.engine.compile('x')
        context=self.context
        self.assertEqual(expr(context), context.vars['x'])

    def testPath(self):
        expr = self.engine.compile('x/y')
        context=self.context
        self.assertEqual(expr(context), context.vars['x'].y)

    def testLongPath(self):
        expr = self.engine.compile('x/y/z')
        context=self.context
        self.assertEqual(expr(context), context.vars['x'].y.z)

    def testOrPath(self):
        expr = self.engine.compile('path:a|b|c/d/e')
        context=self.context
        self.assertEqual(expr(context), 'boot')

        for e in 'Undefined', 'AttributeError', 'LookupError', 'TypeError':
            expr = self.engine.compile('path:ErrorGenerator/%s|b|c/d/e' % e)
            context=self.context
            self.assertEqual(expr(context), 'boot')

    def testDynamic(self):
        expr = self.engine.compile('x/y/?dynamic')
        context=self.context
        self.assertEqual(expr(context),context.vars['x'].y.z)
        
    def testBadInitalDynamic(self):
        from zope.tales.tales import CompilerError
        try:
            self.engine.compile('?x')
        except CompilerError,e:
            self.assertEqual(e.args[0],
                             'Dynamic name specified in first subpath element')
        else:
            self.fail('Engine accepted first subpath element as dynamic')

    def testOldStyleClassIsCalled(self):
        class AnOldStyleClass:
            pass
        self.context.vars['oldstyleclass'] = AnOldStyleClass
        expr = self.engine.compile('oldstyleclass')
        self.assert_(isinstance(expr(self.context), AnOldStyleClass))
            
    def testString(self):
        expr = self.engine.compile('string:Fred')
        context=self.context
        result = expr(context)
        self.assertEqual(result, 'Fred')
        self.failUnless(isinstance(result, str))

    def testStringSub(self):
        expr = self.engine.compile('string:A$B')
        context=self.context
        self.assertEqual(expr(context), 'A2')

    def testStringSub_w_python(self):
        CompilerError = self.engine.getCompilerError()
        self.assertRaises(CompilerError,
                          self.engine.compile,
                                'string:${python:1}')

    def testStringSubComplex(self):
        expr = self.engine.compile('string:a ${x/y} b ${y/z} c')
        context=self.context
        self.assertEqual(expr(context), 'a yikes b 3 c')

    def testStringSubComplex_w_miss_and_python(self):
        # See https://bugs.launchpad.net/zope.tales/+bug/1002242
        CompilerError = self.engine.getCompilerError()
        self.assertRaises(CompilerError,
                          self.engine.compile,
                            'string:${nothig/nothing|python:1}')
 
    def testString8Bits(self):
        # Simple eight bit string interpolation should just work. 
        expr = self.engine.compile('string:a ${eightBits}')
        context=self.context
        self.assertEqual(expr(context), 'a déjà vu')

    def testStringUnicode(self):
        # Unicode string expressions should return unicode strings
        expr = self.engine.compile(u'string:Fred')
        context=self.context
        result = expr(context)
        self.assertEqual(result, u'Fred')
        self.failUnless(isinstance(result, unicode))

    def testStringFailureWhenMixed(self):
        # Mixed Unicode and 8bit string interpolation fails with a
        # UnicodeDecodeError, assuming there is no default encoding
        expr = self.engine.compile(u'string:a ${eightBits}')
        self.assertRaises(UnicodeDecodeError, expr, self.context)

    def testPython(self):
        expr = self.engine.compile('python: 2 + 2')
        context=self.context
        self.assertEqual(expr(context), 4)

    def testPythonCallableIsntCalled(self):
        self.context.vars['acallable'] = lambda: 23
        expr = self.engine.compile('python: acallable')
        self.assertEqual(expr(self.context), self.context.vars['acallable'])

    def testPythonNewline(self):
        expr = self.engine.compile('python: 2 \n+\n 2\n')
        context=self.context
        self.assertEqual(expr(context), 4)

    def testPythonDosNewline(self):
        expr = self.engine.compile('python: 2 \r\n+\r\n 2\r\n')
        context=self.context
        self.assertEqual(expr(context), 4)

    def testPythonErrorRaisesCompilerError(self):
        self.assertRaises(self.engine.getCompilerError(),
                          self.engine.compile, 'python: splat.0')

    def testHybridPathExpressions(self):
        def eval(expr):
            e = self.engine.compile(expr)
            return e(self.context)
        self.context.vars['one'] = 1
        self.context.vars['acallable'] = lambda: 23

        self.assertEqual(eval('foo | python:1+1'), 2)
        self.assertEqual(eval('foo | python:acallable'),
                         self.context.vars['acallable'])
        self.assertEqual(eval('foo | string:x'), 'x')
        self.assertEqual(eval('foo | string:$one'), '1')
        self.assert_(eval('foo | exists:x'))

    def testEmptyPathSegmentRaisesCompilerError(self):
        CompilerError = self.engine.getCompilerError()
        def check(expr):
            self.assertRaises(CompilerError, self.engine.compile, expr)

        # path expressions on their own:
        check('/ab/cd | c/d | e/f')
        check('ab//cd | c/d | e/f')
        check('ab/cd/ | c/d | e/f')
        check('ab/cd | /c/d | e/f')
        check('ab/cd | c//d | e/f')
        check('ab/cd | c/d/ | e/f')
        check('ab/cd | c/d | /e/f')
        check('ab/cd | c/d | e//f')
        check('ab/cd | c/d | e/f/')

        # path expressions embedded in string: expressions:
        check('string:${/ab/cd}')
        check('string:${ab//cd}')
        check('string:${ab/cd/}')
        check('string:foo${/ab/cd | c/d | e/f}bar')
        check('string:foo${ab//cd | c/d | e/f}bar')
        check('string:foo${ab/cd/ | c/d | e/f}bar')
        check('string:foo${ab/cd | /c/d | e/f}bar')
        check('string:foo${ab/cd | c//d | e/f}bar')
        check('string:foo${ab/cd | c/d/ | e/f}bar')
        check('string:foo${ab/cd | c/d | /e/f}bar')
        check('string:foo${ab/cd | c/d | e//f}bar')
        check('string:foo${ab/cd | c/d | e/f/}bar')

    def test_defer_expression_returns_wrapper(self):
        from zope.tales.expressions import DeferWrapper
        expr = self.engine.compile('defer: b')
        context=self.context
        self.failUnless(isinstance(expr(context), DeferWrapper))

    def test_lazy_expression_returns_wrapper(self):
        from zope.tales.expressions import LazyWrapper
        expr = self.engine.compile('lazy: b')
        context=self.context
        self.failUnless(isinstance(expr(context), LazyWrapper))


class FunctionTests(ExpressionTestBase):

    def setUp(self):
        ExpressionTestBase.setUp(self)

        # a test namespace
        class TestNameSpace(object):
            implements(ITALESFunctionNamespace)

            def __init__(self, context):
                self.context = context

            def setEngine(self, engine):
                self._engine = engine

            def engine(self):
                return self._engine

            def upper(self):
                return str(self.context).upper()

            def __getitem__(self,key):
                if key=='jump':
                    return self.context._d
                raise KeyError,key
            
        self.TestNameSpace = TestNameSpace
        self.engine.registerFunctionNamespace('namespace', self.TestNameSpace)

    ## framework-ish tests

    def testSetEngine(self):
        expr = self.engine.compile('adapterTest/namespace:engine')
        self.assertEqual(expr(self.context), self.context)
                
    def testGetFunctionNamespace(self):
        self.assertEqual(
            self.engine.getFunctionNamespace('namespace'),
            self.TestNameSpace
            )

    def testGetFunctionNamespaceBadNamespace(self):
        self.assertRaises(KeyError,
                          self.engine.getFunctionNamespace,
                          'badnamespace')

    ## compile time tests

    def testBadNamespace(self):
        # namespace doesn't exist
        from zope.tales.tales import CompilerError
        try:
            self.engine.compile('adapterTest/badnamespace:title')
        except CompilerError,e:
            self.assertEqual(e.args[0],'Unknown namespace "badnamespace"')
        else:
            self.fail('Engine accepted unknown namespace')

    def testBadInitialNamespace(self):
        # first segment in a path must not have modifier
        from zope.tales.tales import CompilerError
        self.assertRaises(CompilerError,
                          self.engine.compile,
                          'namespace:title')

        # In an ideal world there would be another test here to test
        # that a nicer error was raised when you tried to use
        # something like:
        # standard:namespace:upper
        # ...as a path.
        # However, the compilation stage of PathExpr currently
        # allows any expression type to be nested, so something like:
        # standard:standard:context/attribute
        # ...will work fine.
        # When that is changed so that only expression types which
        # should be nested are nestable, then the additional test
        # should be added here.

    def testInvalidNamespaceName(self):
        from zope.tales.tales import CompilerError
        try:
            self.engine.compile('adapterTest/1foo:bar')
        except CompilerError,e:
            self.assertEqual(e.args[0],
                             'Invalid namespace name "1foo"')
        else:
            self.fail('Engine accepted invalid namespace name')

    def testBadFunction(self):
        # namespace is fine, adapter is not defined
        try:
            expr = self.engine.compile('adapterTest/namespace:title')
            expr(self.context)
        except KeyError,e: 
            self.assertEquals(e.args[0],'title')
        else:
            self.fail('Engine accepted unknown function')

    ## runtime tests
            
    def testNormalFunction(self):
        expr = self.engine.compile('adapterTest/namespace:upper')
        self.assertEqual(expr(self.context), 'YIKES')

    def testFunctionOnFunction(self):
        expr = self.engine.compile('adapterTest/namespace:jump/namespace:upper')
        self.assertEqual(expr(self.context), 'XANDER')

    def testPathOnFunction(self):
        expr = self.engine.compile('adapterTest/namespace:jump/y/z')
        context = self.context
        self.assertEqual(expr(context), context.vars['x'].y.z)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ExpressionTests),
        unittest.makeSuite(FunctionTests),
                        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
