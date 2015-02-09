import unittest

from zope.component.testing import setUp, tearDown
from zope.configuration.xmlconfig import XMLConfig
from zope.testing import doctest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS


def configurationSetUp(test):
    setUp()
    import zope.component
    XMLConfig('meta.zcml', zope.component)()
    import plone.memoize
    XMLConfig('configure.zcml', plone.memoize)()


def test_suite():
    tests = (
        doctest.DocTestSuite('plone.memoize.compress',
                             setUp=configurationSetUp,
                             tearDown=tearDown,
                             optionflags=optionflags),
        doctest.DocFileSuite('instance.txt',
                             package="plone.memoize",
                             setUp=configurationSetUp,
                             tearDown=tearDown,
                             optionflags=optionflags),
        doctest.DocFileSuite('view.txt',
                             package="plone.memoize",
                             setUp=configurationSetUp,
                             tearDown=tearDown,
                             optionflags=optionflags),
        doctest.DocFileSuite('forever.txt',
                             package="plone.memoize",
                             setUp=configurationSetUp,
                             tearDown=tearDown,
                             optionflags=optionflags),
        doctest.DocFileSuite('README.txt'),
        doctest.DocTestSuite('plone.memoize.request',
                             setUp=configurationSetUp,
                             tearDown=tearDown,
                             optionflags=optionflags),
        doctest.DocTestSuite('plone.memoize.volatile'),
        doctest.DocTestSuite('plone.memoize.ram',
                             setUp=configurationSetUp,
                             tearDown=tearDown,
                             optionflags=optionflags),
        )

    return unittest.TestSuite(tests)
