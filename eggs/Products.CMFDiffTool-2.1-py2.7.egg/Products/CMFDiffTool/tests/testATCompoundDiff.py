import BaseTestCase

if BaseTestCase.HAS_PLONE:
    from at_compound_tests import TestATCompoundDiff

    def test_suite():
        import unittest
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestATCompoundDiff))
        return suite
