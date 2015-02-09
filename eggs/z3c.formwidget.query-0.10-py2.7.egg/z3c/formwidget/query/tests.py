import doctest
import unittest
from zope import interface, component, schema
from zope.testing.cleanup import cleanUp
from z3c.form import testing


def setUp(test):
    testing.setUp(test)
    test.globs.update(dict(
        interface=interface,
        component=component,
        schema=schema))


def tearDown(test):
    cleanUp()


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
