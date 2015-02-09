import zope.component.testing
from zope.testing import doctest
from zope.testing.doctestunit import DocFileSuite


def tearDown(test):
    zope.component.testing.tearDown(test)


def test_suite():
    from unittest import TestSuite
    suite = TestSuite()
    suite.addTests((
        DocFileSuite('storage.txt',
                     tearDown=tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        ),
        DocFileSuite('manager.txt',
                     tearDown=tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        ),
    ))
    return suite
