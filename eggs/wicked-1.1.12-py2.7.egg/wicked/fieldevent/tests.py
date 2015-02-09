import unittest, doctest
from wicked.fieldevent import test_suite as rm
from wicked.fieldevent.meta import test_suite as meta

def test_suite():
    return unittest.TestSuite((rm(), meta()))
