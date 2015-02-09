import doctest
from unittest import TestSuite

from Products.PloneTestCase import PloneTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite

# BBB Zope 2.12
try:
    from Testing.testbrowser import Browser
    Browser # pyflakes
except ImportError:
    from Products.Five.testbrowser import Browser

from plone.app.customerize.tests import layer

PloneTestCase.setupPloneSite()


class CustomerizeFunctionalTestCase(PloneTestCase.FunctionalTestCase):

    layer = layer.PloneCustomerize

    def afterSetUp(self):
        """ set up the tests """
        pass

    def getBrowser(self, loggedIn=False):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser()
        if loggedIn:
            user = PloneTestCase.default_user
            pwd = PloneTestCase.default_password
            browser.addHeader('Authorization', 'Basic %s:%s' % (user, pwd))
        return browser


def test_suite():
    suite = TestSuite()
    OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    for testfile in ('testBrowserLayers.txt', 'testCustomizeView.txt'):
        suite.addTest(FunctionalDocFileSuite(testfile,
                                optionflags=OPTIONFLAGS,
                                package="plone.app.customerize.tests",
                                test_class=CustomerizeFunctionalTestCase),
                     )
    return suite
