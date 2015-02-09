import unittest
from zope.testing import doctest

def test_suite():
    from Testing.ZopeTestCase import ZopeDocFileSuite
    try:
        from Products.PloneTestCase.layer import ZCMLLayer
    except ImportError:
        from collective.testing.layer import ZCMLLayer
    suite = ZopeDocFileSuite('README.txt',
                             package="wicked.atcontent",
                             optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
                             )
    suite.layer = ZCMLLayer
    return unittest.TestSuite((suite))


