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
"""ExceptionFormatter tests.
"""

import sys
from unittest import TestCase, makeSuite

from zope.exceptions.exceptionformatter import format_exception


def tb(as_html=0):
    t, v, b = sys.exc_info()
    try:
        return ''.join(format_exception(t, v, b, as_html=as_html))
    finally:
        del b


class ExceptionForTesting (Exception):
    pass


class TestingTracebackSupplement(object):

    source_url = '/somepath'
    line = 634
    column = 57
    warnings = ['Repent, for the end is nigh']

    def __init__(self, expression):
        self.expression = expression


class Test(TestCase):

    def testBasicNamesText(self, as_html=0):
        try:
            raise ExceptionForTesting
        except ExceptionForTesting:
            s = tb(as_html)
            # The traceback should include the name of this function.
            self.assertTrue(s.find('testBasicNamesText') >= 0)
            # The traceback should include the name of the exception.
            self.assertTrue(s.find('ExceptionForTesting') >= 0)
        else:
            self.fail('no exception occurred')

    def testBasicNamesHTML(self):
        self.testBasicNamesText(1)

    def testSupplement(self, as_html=0):
        try:
            __traceback_supplement__ = (TestingTracebackSupplement,
                                        "You're one in a million")
            raise ExceptionForTesting
        except ExceptionForTesting:
            s = tb(as_html)
            # The source URL
            self.assertTrue(s.find('/somepath') >= 0, s)
            # The line number
            self.assertTrue(s.find('634') >= 0, s)
            # The column number
            self.assertTrue(s.find('57') >= 0, s)
            # The expression
            self.assertTrue(s.find("You're one in a million") >= 0, s)
            # The warning
            self.assertTrue(s.find("Repent, for the end is nigh") >= 0, s)
        else:
            self.fail('no exception occurred')

    def testSupplementHTML(self):
        self.testSupplement(1)

    def testTracebackInfo(self, as_html=0):
        try:
            __traceback_info__ = "Adam & Eve"
            raise ExceptionForTesting
        except ExceptionForTesting:
            s = tb(as_html)
            if as_html:
                # Be sure quoting is happening.
                self.assertTrue(s.find('Adam &amp; Eve') >= 0, s)
            else:
                self.assertTrue(s.find('Adam & Eve') >= 0, s)
        else:
            self.fail('no exception occurred')

    def testTracebackInfoHTML(self):
        self.testTracebackInfo(1)

    def testTracebackInfoTuple(self):
        try:
            __traceback_info__ = ("Adam", "Eve")
            raise ExceptionForTesting
        except ExceptionForTesting:
            s = tb()
            self.assertTrue(s.find('Adam') >= 0, s)
            self.assertTrue(s.find('Eve') >= 0, s)
        else:
            self.fail('no exception occurred')

    def testMultipleLevels(self):
        # Makes sure many levels are shown in a traceback.
        def f(n):
            """Produces a (n + 1)-level traceback."""
            __traceback_info__ = 'level%d' % n
            if n > 0:
                f(n - 1)
            else:
                raise ExceptionForTesting

        try:
            f(10)
        except ExceptionForTesting:
            s = tb()
            for n in range(11):
                self.assertTrue(s.find('level%d' % n) >= 0, s)
        else:
            self.fail('no exception occurred')

    def testQuoteLastLine(self):
        class C(object):
            pass
        try:
            raise TypeError(C())
        except:
            s = tb(1)
        else:
            self.fail('no exception occurred')
        self.assertTrue(s.find('&lt;') >= 0, s)
        self.assertTrue(s.find('&gt;') >= 0, s)

    def testMultilineException(self):
        try:
            exec 'syntax error\n'
        except Exception:
            s = tb()
        self.assertEqual(s.splitlines()[-3:],
                         ['    syntax error',
                          '               ^',
                          'SyntaxError: invalid syntax'])

    def testRecursionFailure(self):
        from zope.exceptions.exceptionformatter import TextExceptionFormatter

        class FormatterException(Exception):
            pass
            
        class FailingFormatter(TextExceptionFormatter):
            def formatLine(self, tb):
                raise FormatterException("Formatter failed")

        fmt = FailingFormatter()
        try:
            raise ExceptionForTesting
        except ExceptionForTesting:
            try:
                fmt.formatException(*sys.exc_info())
            except FormatterException:
                s = tb()
        # Recursion was detected
        self.assertTrue('(Recursive formatException() stopped, trying traceback.format_tb)' in s, s)
        # and we fellback to the stdlib rather than hid the real error
        self.assertEqual(s.splitlines()[-2], '    raise FormatterException("Formatter failed")')
        self.assertTrue('FormatterException: Formatter failed' in s.splitlines()[-1])

def test_suite():
    return makeSuite(Test)
