##############################################################################
#
# Copyright (c) 2003-2009 Zope Foundation and Contributors.
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
"""Location support tests
"""

import doctest
import unittest


def test_suite():
    suite = unittest.TestSuite((
        doctest.DocFileSuite('location.txt'),
        doctest.DocTestSuite('zope.location.traversing'),
    ))

    try:
        import zope.configuration
    except ImportError:
        pass
    else:
        suite.addTest(doctest.DocFileSuite('configure.txt'))

    return suite
