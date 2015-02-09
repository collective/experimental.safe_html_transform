##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Visible Source
# License, Version 1.0 (ZVSL).  A copy of the ZVSL should accompany this
# distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Run all Zope Version Control tests

$Id: test_all.py 113728 2010-06-21 15:10:46Z ctheune $"""

import unittest

from Products.ZopeVersionControl.tests import testVersionControl

try:
    from Products import References
except ImportError:
    # References product is not available
    testReferenceVersioning = None
else:
    # References product is available
    from Products.ZopeVersionControl.tests import testReferenceVersioning


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(testVersionControl.test_suite())
    if testReferenceVersioning is not None:
        suite.addTest(testReferenceVersioning.test_suite())
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
