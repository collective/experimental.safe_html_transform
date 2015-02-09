import doctest
import unittest

from plone.session import tktauth

optionflags = doctest.ELLIPSIS


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(tktauth, optionflags=optionflags))
    return suite
