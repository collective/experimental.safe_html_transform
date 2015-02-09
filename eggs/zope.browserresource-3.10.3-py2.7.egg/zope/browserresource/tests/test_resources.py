##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Test Browser Resources

$Id: test_resources.py 111698 2010-04-30 20:23:50Z hannosch $
"""

import doctest
import unittest
from zope.testing import cleanup

def setUp(test):
    cleanup.setUp()

def tearDown(test):
    cleanup.tearDown()

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(
            'zope.browserresource.resources',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE),
        ))
