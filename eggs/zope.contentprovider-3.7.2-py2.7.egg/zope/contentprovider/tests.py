##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""Content provider tests

$Id: tests.py 112004 2010-05-05 17:54:28Z tseaver $
"""
__docformat__ = 'restructuredtext'

import doctest
import os.path
import unittest

from zope.component import eventtesting
from zope.testing import cleanup

counter = 0
mtime_func = None

def setUp(test):
    cleanup.setUp()
    eventtesting.setUp()

    from zope.browserpage.metaconfigure import registerType
    from zope.contentprovider import tales
    registerType('provider', tales.TALESProviderExpression)

    # Make sure we are always reloading page template files ;-)
    global mtime_func
    mtime_func = os.path.getmtime
    def number(x):
        global counter
        counter += 1
        return counter
    os.path.getmtime = number


def tearDown(test):
    cleanup.tearDown()
    os.path.getmtime = mtime_func
    global counter
    counter = 0

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
            globs = {'__file__': os.path.join(
                os.path.dirname(__file__), 'README.txt')}
            ),
        ))
