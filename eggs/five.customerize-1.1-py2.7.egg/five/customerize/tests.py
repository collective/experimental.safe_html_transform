from unittest import TestSuite, main
from Testing.ZopeTestCase import ZopeDocFileSuite
from Testing.ZopeTestCase import FunctionalDocFileSuite

from zope.component import testing, provideAdapter
from zope.traversing.adapters import DefaultTraversable
from zope.publisher.browser import BrowserLanguages
from zope.publisher.http import HTTPCharsets
from zope.site.hooks import setHooks

# BBB Zope 2.12
try:
    from Zope2.App.zcml import load_config
    load_config # pyflakes
except ImportError:
    from Products.Five.zcml import load_config


def setUp(test):
    testing.setUp(test)
    provideAdapter(DefaultTraversable, (None,))
    provideAdapter(BrowserLanguages)
    provideAdapter(HTTPCharsets)

    import Products.Five
    import five.customerize
    load_config('configure.zcml', package=Products.Five)
    load_config('configure.zcml', package=five.customerize)
    setHooks()


def test_suite():
    return TestSuite([
        ZopeDocFileSuite('zpt.txt', package="five.customerize",
                         setUp=setUp, tearDown=testing.tearDown),
        ZopeDocFileSuite('customerize.txt', package="five.customerize",
                         setUp=setUp),
        FunctionalDocFileSuite('browser.txt', package="five.customerize",
                               setUp=setUp)
        ])

if __name__ == '__main__':
    main(defaultTest='test_suite')
