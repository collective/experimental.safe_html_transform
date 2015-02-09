from zope.interface import alsoProvides
from Products.CMFCore.interfaces import IDublinCore
from Products.CMFCore.utils import getToolInterface

from Products.PloneLanguageTool import LanguageTool
from Products.PloneLanguageTool.interfaces import ILanguageTool
from Products.PloneLanguageTool.tests import base


class TestLanguageToolExists(base.TestCase):

    def afterSetUp(self):
        self.tool_id = LanguageTool.id

    def testLanguageToolExists(self):
        self.failUnless(self.tool_id in self.portal.objectIds())


class TestLanguageToolSettings(base.TestCase):

    def afterSetUp(self):
        self.tool_id = LanguageTool.id
        self.ltool = self.portal._getOb(self.tool_id)

    def testLanguageToolType(self):
        self.failUnless(self.ltool.meta_type == LanguageTool.meta_type)

    def testSetLanguageSettings(self):
        defaultLanguage = 'de'
        supportedLanguages = ['en','de','no']
        self.ltool.manage_setLanguageSettings(defaultLanguage, supportedLanguages,
                                   setContentN=False,
                                   setCookieN=False, setCookieEverywhere=False,
                                   setRequestN=False,
                                   setPathN=False, setForcelanguageUrls=False,
                                   setAllowContentLanguageFallback=True,
                                   setUseCombinedLanguageCodes=True,
                                   startNeutral=False, displayFlags=False,
                                   setCcTLDN=True, setSubdomainN=True,
                                   setAuthOnlyN=True)

        self.failUnless(self.ltool.getDefaultLanguage()==defaultLanguage)
        self.failUnless(self.ltool.getSupportedLanguages()==supportedLanguages)
        self.failUnless(self.ltool.use_content_negotiation==False)
        self.failUnless(self.ltool.use_cookie_negotiation==False)
        self.failUnless(self.ltool.set_cookie_everywhere==False)
        self.failUnless(self.ltool.use_request_negotiation==False)
        self.failUnless(self.ltool.use_path_negotiation==False)
        self.failUnless(self.ltool.force_language_urls==False)
        self.failUnless(self.ltool.allow_content_language_fallback==True)
        self.failUnless(self.ltool.use_combined_language_codes==True)
        self.failUnless(self.ltool.startNeutral()==False)
        self.failUnless(self.ltool.showFlags()==False)
        self.failUnless(self.ltool.use_cctld_negotiation==True)
        self.failUnless(self.ltool.use_subdomain_negotiation==True)
        self.failUnless(self.ltool.authenticated_users_only==True)


class TestLanguageTool(base.TestCase):

    def afterSetUp(self):
        self.tool_id = LanguageTool.id
        self.ltool = self.portal._getOb(self.tool_id)

    def testLanguageSettings(self):
        defaultLanguage = 'de'
        supportedLanguages = ['en','de','no']
        self.ltool.manage_setLanguageSettings(defaultLanguage, supportedLanguages,
                                              setUseCombinedLanguageCodes=False)
        self.failUnless(self.ltool.getDefaultLanguage()==defaultLanguage)
        self.failUnless(self.ltool.getSupportedLanguages()==supportedLanguages)

    def testSupportedLanguages(self):
        defaultLanguage = 'de'
        supportedLanguages = ['en','de','no']
        self.ltool.manage_setLanguageSettings(defaultLanguage, supportedLanguages)
        self.failUnless(self.ltool.getSupportedLanguages()==supportedLanguages)

        self.ltool.removeSupportedLanguages(supportedLanguages)
        self.failUnless(self.ltool.getSupportedLanguages()==[])

        for lang in supportedLanguages:
            self.ltool.addSupportedLanguage(lang)
        self.failUnless(self.ltool.getSupportedLanguages()==supportedLanguages)

    def testDefaultLanguage(self):
        supportedLanguages = ['de','no']

        self.ltool.manage_setLanguageSettings('no', supportedLanguages)
        self.failUnless(self.ltool.getSupportedLanguages()==supportedLanguages)
        self.failUnless(self.ltool.getDefaultLanguage()=='no')

        # default not in supported languages, should set to first supported
        self.ltool.manage_setLanguageSettings('nl', supportedLanguages)

        self.failUnless(self.ltool.getSupportedLanguages()==supportedLanguages)
        self.failUnless(self.ltool.getDefaultLanguage()=='de')

    def testAvailableLanguage(self):
        defaultLanguage = 'de'
        supportedLanguages = ['en','de','no']
        self.ltool.manage_setLanguageSettings(defaultLanguage, supportedLanguages)
        availableLanguages = self.ltool.getAvailableLanguageInformation()
        for lang in availableLanguages:
            if lang in supportedLanguages:
                self.failUnless(availableLanguages[lang]['selected'] == True)

    def testGetContentLanguage(self):
        # tests for issue #11263
        defaultLanguage = 'de'
        supportedLanguages = ['en','de','no']
        self.ltool.manage_setLanguageSettings(defaultLanguage, supportedLanguages)
        self.ltool.REQUEST.path = ['Members',]
        content = self.portal.Members
        content.setLanguage('de')
        alsoProvides(content, IDublinCore)
        self.ltool.getContentLanguage()
        self.failUnless(self.ltool.getContentLanguage()=='de')
        self.ltool.REQUEST.path = ['view', 'foo.jpg', 'Members',]
        self.failUnless(self.ltool.getContentLanguage()=='de')
        self.ltool.REQUEST.path = ['foo.jpg', 'Members',]
        self.failUnless(self.ltool.getContentLanguage()==None)
        self.ltool.REQUEST.path = ['foo', 'portal_javascript',]
        self.failUnless(self.ltool.getContentLanguage()==None)

    def testRegisterInterface(self):
        iface = getToolInterface('portal_languages')
        self.assertEqual(iface, ILanguageTool)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestLanguageToolExists))
    suite.addTest(makeSuite(TestLanguageToolSettings))
    suite.addTest(makeSuite(TestLanguageTool))
    return suite
