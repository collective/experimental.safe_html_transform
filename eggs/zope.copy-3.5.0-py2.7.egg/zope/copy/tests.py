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
"""Tests for the zope.copy package.

$Id: tests.py 96251 2009-02-08 16:17:47Z nadako $
"""
import unittest
from zope.testing import doctest, module

def setUp(test):
    module.setUp(test, 'zope.copy.doctest')

def tearDown(test):
    module.tearDown(test)

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
            setUp=setUp,
            tearDown=tearDown,
            optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE),
        ))
