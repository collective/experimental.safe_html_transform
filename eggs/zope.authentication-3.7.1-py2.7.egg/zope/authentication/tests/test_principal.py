##############################################################################
#
# Copyright (c) 2009 Zope Corporation and Contributors.
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
"""Test for principal lookup related functionality

$Id: test_principal.py 111660 2010-04-30 17:27:53Z hannosch $
"""
import doctest
import unittest


def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.authentication.principal'),
        doctest.DocFileSuite('../principalterms.txt'),
        ))
