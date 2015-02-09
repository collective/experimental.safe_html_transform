import unittest

from zope.testing import doctestunit
from zope.component import testing


class TestWrapperUpdate(unittest.TestCase):

    def test_wrapper_update(self):
        from plone.indexer import indexer
        from zope.interface import Interface

        @indexer(Interface)
        def my_func(obj):
            """My custom docstring."""

        self.assertEqual(my_func.__doc__, 'My custom docstring.')
        self.assertEqual(my_func.__module__, 'plone.indexer.tests')
        self.assertEqual(my_func.__name__, 'my_func')


def test_suite():
    return unittest.TestSuite([
        doctestunit.DocFileSuite(
            'README.txt', package='plone.indexer',
            setUp=testing.setUp, tearDown=testing.tearDown),
        unittest.makeSuite(TestWrapperUpdate),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
