##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Test the Dublin Core Property implementation
"""
__docformat__ = "reStructuredText"

import doctest
import unittest
from zope import component
from zope.testing import cleanup
from zope.annotation.attribute import AttributeAnnotations
from zope.dublincore import testing


def setUp(test):
    cleanup.setUp()
    component.provideAdapter(AttributeAnnotations)
    testing.setUpDublinCore()


def tearDown(test):
    cleanup.tearDown()


def test_suite():
    return unittest.TestSuite(
        (
        doctest.DocFileSuite(
            '../property.txt',
             setUp=setUp,
             tearDown=tearDown,
           optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
           ),
        ))
