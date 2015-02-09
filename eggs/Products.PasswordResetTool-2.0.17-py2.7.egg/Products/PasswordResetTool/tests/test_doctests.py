"""
PasswordResetTool doctests
"""

import doctest
import unittest
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.PloneTestCase import PloneTestCase
from Products.MailHost.interfaces import IMailHost
from zope.component import getSiteManager
from Acquisition import aq_base

PloneTestCase.setupPloneSite()

from Products.CMFPlone.tests.utils import MockMailHost


OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

class MockMailHostTestCase(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.portal._original_MailHost = self.portal.MailHost
        self.portal.MailHost = mailhost = MockMailHost('MailHost')
        mailhost.smtp_host = 'localhost'
        sm = getSiteManager(context=self.portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(mailhost, provided=IMailHost)
        self.portal.email_from_address = 'test@example.com'

    def beforeTearDown(self):
        self.portal.MailHost = self.portal._original_MailHost
        sm = getSiteManager(context=self.portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(aq_base(self.portal._original_MailHost), provided=IMailHost)


def test_suite():
    return unittest.TestSuite((
        FunctionalDocFileSuite('browser.txt',
                               optionflags=OPTIONFLAGS,
                               package='Products.PasswordResetTool.tests',
                               test_class=MockMailHostTestCase),
        FunctionalDocFileSuite('view.txt',
                               optionflags=OPTIONFLAGS,
                               package='Products.PasswordResetTool.tests',
                               test_class=MockMailHostTestCase),
        ))
