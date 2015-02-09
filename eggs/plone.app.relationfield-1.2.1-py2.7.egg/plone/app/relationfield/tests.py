import unittest
from zope.testing import doctest
import zope.component.testing

class UnitTestLayer:
    
    @classmethod
    def testTearDown(cls):
        zope.component.testing.tearDown()

def test_suite():
    
    marshaler = doctest.DocFileSuite('marshaler.txt', optionflags=doctest.ELLIPSIS)
    marshaler.layer = UnitTestLayer
    
    return unittest.TestSuite((marshaler,))
