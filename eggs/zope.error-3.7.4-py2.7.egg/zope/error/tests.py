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
"""Error Reporting Utility Tests
"""
import sys
import unittest

from zope.exceptions.exceptionformatter import format_exception
from zope.testing import cleanup

from zope.error.error import ErrorReportingUtility, getFormattedException


class Error(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


def getAnErrorInfo(value=""):
    try:
        raise Error(value)
    except:
        return sys.exc_info()


class TestRequest(object):
    """Mock request that mimics the zope.publisher request."""

    def __init__(self, environ=None):
        self._environ = environ or {}

    def setPrincipal(self, principal):
        self.principal = principal

    def items(self):
        return []


class ErrorReportingUtilityTests(cleanup.CleanUp, unittest.TestCase):

    def test_checkForEmptyLog(self):
        # Test Check Empty Log
        errUtility = ErrorReportingUtility()
        getProp = errUtility.getLogEntries()
        self.failIf(getProp)

    def test_checkProperties(self):
        # Test Properties test
        errUtility = ErrorReportingUtility()
        setProp = {
            'keep_entries':10,
            'copy_to_zlog':1,
            'ignored_exceptions':()
            }
        errUtility.setProperties(**setProp)
        getProp = errUtility.getProperties()
        self.assertEqual(setProp, getProp)

    def test_ErrorLog(self):
        # Test for Logging Error.  Create one error and check whether its
        # logged or not.
        errUtility = ErrorReportingUtility()
        exc_info = getAnErrorInfo()
        errUtility.raising(exc_info)
        getErrLog = errUtility.getLogEntries()
        self.assertEquals(1, len(getErrLog))

        tb_text = ''.join(format_exception(as_html=0, *exc_info))

        err_id = getErrLog[0]['id']
        self.assertEquals(tb_text,
                          errUtility.getLogEntryById(err_id)['tb_text'])

    def test_ErrorLog_unicode(self):
        # Emulate a unicode url, it gets encoded to utf-8 before it's passed
        # to the request. Also add some unicode field to the request's
        # environment and make the principal's title unicode.
        request = TestRequest(environ={'PATH_INFO': '/\xd1\x82',
                                       'SOME_UNICODE': u'\u0441'})
        class PrincipalStub(object):
            id = u'\u0441'
            title = u'\u0441'
            description = u'\u0441'
        request.setPrincipal(PrincipalStub())

        errUtility = ErrorReportingUtility()
        exc_info = getAnErrorInfo(u"Error (\u0441)")
        errUtility.raising(exc_info, request=request)
        getErrLog = errUtility.getLogEntries()
        self.assertEquals(1, len(getErrLog))

        tb_text = getFormattedException(exc_info)

        err_id = getErrLog[0]['id']
        self.assertEquals(tb_text,
                          errUtility.getLogEntryById(err_id)['tb_text'])

        username = getErrLog[0]['username']
        self.assertEquals(username, u'unauthenticated, \u0441, \u0441, \u0441')

    def test_ErrorLog_nonascii(self):
        # Emulate a unicode url, it gets encoded to utf-8 before it's passed
        # to the request. Also add some unicode field to the request's
        # environment and make the principal's title unicode.
        request = TestRequest(environ={'PATH_INFO': '/\xd1\x82',
                                       'SOME_NONASCII': '\xe1'})
        class PrincipalStub(object):
            id = '\xe1'
            title = '\xe1'
            description = '\xe1'
        request.setPrincipal(PrincipalStub())

        errUtility = ErrorReportingUtility()
        exc_info = getAnErrorInfo("Error (\xe1)")
        errUtility.raising(exc_info, request=request)
        getErrLog = errUtility.getLogEntries()
        self.assertEquals(1, len(getErrLog))

        tb_text = getFormattedException(exc_info)

        err_id = getErrLog[0]['id']
        self.assertEquals(tb_text,
                          errUtility.getLogEntryById(err_id)['tb_text'])

        username = getErrLog[0]['username']
        self.assertEquals(username, r"unauthenticated, \xe1, \xe1, \xe1")


class GetPrintableTests(unittest.TestCase):
    """Testing .error.getPrintable(value)"""

    def getPrintable(self, value):
        from zope.error.error import getPrintable
        return getPrintable(value)

    def test_xml_tags_get_escaped(self):
        self.assertEqual(u'&lt;script&gt;', self.getPrintable(u'<script>'))

    def test_str_values_get_converted_to_unicode(self):
        self.assertEqual(u'\\u0441', self.getPrintable('\u0441'))
        self.assertTrue(isinstance(self.getPrintable('\u0441'), unicode))

    def test_non_str_values_get_converted_using_a_str_call(self):
        class NonStr(object):
            def __str__(self):
                return 'non-str'
        self.assertEqual(u'non-str', self.getPrintable(NonStr()))
        self.assertTrue(isinstance(self.getPrintable(NonStr()), unicode))

    def test_non_str_those_conversion_fails_are_returned_specially(self):
        class NonStr(object):
            def __str__(self):
                raise ValueError('non-str')
        self.assertEqual(
                u'<unprintable NonStr object>', self.getPrintable(NonStr()))
        self.assertTrue(isinstance(self.getPrintable(NonStr()), unicode))

    def test_non_str_those_conversion_fails_are_returned_with_escaped_name(
            self):
        class NonStr(object):
            def __str__(self):
                raise ValueError('non-str')
        NonStr.__name__ = '<script>'
        self.assertEqual(u'<unprintable &lt;script&gt; object>',
                         self.getPrintable(NonStr()))
