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
"""Test permissions

$Id: test_permission.py 111761 2010-04-30 21:52:52Z hannosch $
"""
import unittest
from doctest import DocTestSuite

from zope.component.testing import setUp, tearDown

__docformat__ = "reStructuredText"

def test_suite():
    return unittest.TestSuite([
        DocTestSuite('zope.security.permission',
                     setUp=setUp, tearDown=tearDown),
        ])
