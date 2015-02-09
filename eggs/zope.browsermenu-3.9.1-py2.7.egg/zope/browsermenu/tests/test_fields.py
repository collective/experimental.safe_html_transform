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
"""Test fields.

$Id: test_fields.py 111004 2010-04-16 20:13:36Z tseaver $
"""
import unittest
import doctest
from zope.testing import cleanup

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.browsermenu.field',
                     setUp=lambda test:cleanup.setUp(),
                     tearDown=lambda test:cleanup.tearDown()),
        ))
