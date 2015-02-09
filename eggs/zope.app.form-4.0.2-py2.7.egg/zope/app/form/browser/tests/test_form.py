##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Tests for the ZCML Documentation Module

$Id: test_form.py 107401 2009-12-30 22:56:20Z faassen $
"""
import unittest
import doctest

from zope.schema.interfaces import ITextLine
from zope.component import testing

from zope.app.testing import ztapi

from zope.app.form.browser import TextWidget
from zope.formlib.interfaces import IInputWidget

def setUp(test):
    testing.setUp()
    ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../form.txt',
                             setUp=setUp, tearDown=testing.tearDown,
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
