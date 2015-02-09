import doctest
import unittest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(
            'archetypes.referencebrowserwidget.utils',
            ))
    return suite
