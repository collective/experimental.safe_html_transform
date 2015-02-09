from Products.PloneLanguageTool import LanguageTool
from Products.PloneLanguageTool.tests import base

from Products.CMFTestCase.ctc import default_password
from Products.CMFTestCase.ctc import default_user


class LanguageNegotiationTestCase(base.FunctionalTestCase):

    def afterSetUp(self):
        self.basic_auth = '%s:%s' % (default_user, default_password)
        self.portal_path = self.portal.absolute_url(1)
        self.tool = self.portal[LanguageTool.id]
        self.tool.always_show_selector = 1
        self.tool.set_cookie_everywhere = 1

    def checkLanguage(self, response, language):
        self.assertEquals(response.getStatus(), 200)
        cookie = response.getCookie('I18N_LANGUAGE')['value']
        self.assertEquals(cookie, language)


class TestDefaultLanguageNegotiation(LanguageNegotiationTestCase):

    def testLanguageNegotiation(self):
        # Once PLT is installed only English is allowed as a language
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'pt'})
        self.checkLanguage(response, "en")


class TestNoCombinedLanguageNegotiation(LanguageNegotiationTestCase):

    def afterSetUp(self):
        LanguageNegotiationTestCase.afterSetUp(self)
        # set some allowed languages and make sure we don't use combined
        # language codes
        self.tool.supported_langs = ['en', 'pt', 'de']
        self.tool.use_request_negotiation = 1
        self.tool.use_combined_language_codes = 0
        self.tool.display_flags = 0

    def testLanguageNegotiation(self):
        # Test simple supported codes
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'pt'})
        self.checkLanguage(response, "pt")

        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'de'})
        self.checkLanguage(response, "de")

        # Test combined unsupported codes, should fall back
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'pt-br'})
        self.checkLanguage(response, "pt")


class TestCombinedLanguageNegotiation(LanguageNegotiationTestCase):

    def afterSetUp(self):
        LanguageNegotiationTestCase.afterSetUp(self)
        # set some allowed languages and make sure we don't use combined
        # language codes
        self.tool.supported_langs = ['en', 'pt', 'de', 'pt-br']
        self.tool.use_request_negotiation = 1
        self.tool.use_combined_language_codes = 1
        self.tool.display_flags = 0

    def testLanguageNegotiation(self):
        # Test simple supported codes
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'pt'})
        self.checkLanguage(response, "pt")

        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'de'})
        self.checkLanguage(response, "de")

        # Test combined supported codes
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'pt-br'})
        self.checkLanguage(response, "pt-br")

        # Test combined unsupported codes, should fall back
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'de-de'})
        self.checkLanguage(response, "de")


class TestContentLanguageNegotiation(LanguageNegotiationTestCase):

    def afterSetUp(self):
        LanguageNegotiationTestCase.afterSetUp(self)
        self.tool.supported_langs = ['en', 'nl', 'fr']
        self.tool.use_content_negotiation = 1
        self.tool.display_flags = 0

    def testContentObject(self):
        self.folder.invokeFactory('Document', 'doc')
        doc = self.folder.doc
        doc.setLanguage('nl')
        self.failUnlessEqual(doc.Language(), 'nl')
        docpath = '/'.join(doc.getPhysicalPath())
        response = self.publish(docpath, self.basic_auth,
                                env={'PATH_INFO': docpath})
        self.checkLanguage(response, "nl")

    def testContentObjectVHMPortal(self):
        adding = self.app.manage_addProduct['SiteAccess']
        adding.manage_addVirtualHostMonster('VHM')
        vhmBasePath = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/" % self.portal.getId()
        vhmBaseUrl = 'http://example.org/'

        self.folder.invokeFactory('Folder', 'sub')
        sub = self.folder['sub']
        sub.setLanguage('nl')
        sub.invokeFactory('Document', 'doc')
        doc = sub.doc
        doc.setLanguage('nl')
        self.failUnlessEqual(doc.Language(), 'nl')
        docpath = '/'.join(self.portal.portal_url.getRelativeContentPath(doc))
        response = self.publish(vhmBasePath + docpath, self.basic_auth)
        self.checkLanguage(response, "nl")

    def testContentObjectVHMPortalVHSubpath(self):
        adding = self.app.manage_addProduct['SiteAccess']
        adding.manage_addVirtualHostMonster('VHM')
        vhmBasePath = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_one/_vh_two/" % self.portal.getId()
        vhmBaseUrl = 'http://example.org/'

        self.folder.invokeFactory('Folder', 'sub')
        sub = self.folder['sub']
        sub.setLanguage('nl')
        sub.invokeFactory('Document', 'doc')
        doc = sub.doc
        doc.setLanguage('nl')
        self.failUnlessEqual(doc.Language(), 'nl')
        docpath = '/'.join(self.portal.portal_url.getRelativeContentPath(doc))
        response = self.publish(vhmBasePath + docpath, self.basic_auth)
        self.checkLanguage(response, "nl")


    def testContentObjectVHMFolder(self):
        adding = self.app.manage_addProduct['SiteAccess']
        adding.manage_addVirtualHostMonster('VHM')

        folder_path = '/'.join(self.folder.getPhysicalPath())
        vhmBasePath = "/VirtualHostBase/http/example.org:80%s/VirtualHostRoot/" % folder_path
        vhmBaseUrl = 'http://example.org/'

        self.folder.invokeFactory('Folder', 'sub')
        sub = self.folder['sub']
        sub.setLanguage('nl')
        sub.invokeFactory('Document', 'doc')
        doc = sub.doc
        doc.setLanguage('nl')
        self.failUnlessEqual(doc.Language(), 'nl')
        docpath = '/'.join(doc.getPhysicalPath())
        docpath = docpath[len(folder_path)+1:]
        response = self.publish(vhmBasePath + docpath, self.basic_auth)
        self.checkLanguage(response, "nl")


class TestCcTLDLanguageNegotiation(LanguageNegotiationTestCase):

    def afterSetUp(self):
        LanguageNegotiationTestCase.afterSetUp(self)
        self.tool.supported_langs = ['en', 'nl', 'fr']
        self.tool.use_cctld_negotiation = 1
        self.tool.display_flags = 0

    def testSimpleHostname(self):
        # For a simple hostname without ccTLD the canonical language is used
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'localhost'})
        self.checkLanguage(response, "en")

    def testIPAddress(self):
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': '127.0.0.1'})
        self.checkLanguage(response, "en")

    def testDutchDomain(self):
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'plone.nl'})
        self.checkLanguage(response, "nl")

    def testAcceptedLanguages(self):
        # Brazil uses Portugese, which is not in the accepted languages list
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'plone.br'})
        self.checkLanguage(response, "en")

    def testMultiLingualCountries(self):
        # Some countries refuse to pick a single language. Belgium
        # uses both Dutch and French, with a preference for Dutch.

        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'plone.be'})
        self.checkLanguage(response, "nl")

        # If we stop allowing Dutch we should now fall back to French
        self.tool.supported_langs = ['en', 'fr']
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'plone.be'})
        self.checkLanguage(response, "fr")


class TestSubdomainLanguageNegotiation(LanguageNegotiationTestCase):

    def afterSetUp(self):
        LanguageNegotiationTestCase.afterSetUp(self)
        self.tool.supported_langs = ['en', 'nl', 'fr']
        self.tool.use_subdomain_negotiation = 1
        self.tool.display_flags = 0

    def testSimpleHostname(self):
        # For a simple hostname without ccTLD the canonical language is used
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'localhost'})
        self.checkLanguage(response, "en")

    def testIPAddress(self):
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': '127.0.0.1'})
        self.checkLanguage(response, "en")

    def testDutchDomain(self):
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'nl.plone.org'})
        self.checkLanguage(response, "nl")

    def testAcceptedLanguages(self):
        # Brazil uses Portugese, which is not in the accepted languages list
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'br.plone.org'})
        self.checkLanguage(response, "en")

    def testMultiLingualCountries(self):
        # Some countries refuse to pick a single language. Belgium
        # uses both Dutch and French, with a preference for Dutch.

        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'be.plone.org'})
        self.checkLanguage(response, "nl")

        # If we stop allowing Dutch we should now fall back to French
        self.tool.supported_langs = ['en', 'fr']
        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_HOST': 'be.plone.org'})
        self.checkLanguage(response, "fr")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestDefaultLanguageNegotiation))
    suite.addTest(makeSuite(TestNoCombinedLanguageNegotiation))
    suite.addTest(makeSuite(TestCombinedLanguageNegotiation))
    suite.addTest(makeSuite(TestContentLanguageNegotiation))
    suite.addTest(makeSuite(TestCcTLDLanguageNegotiation))
    suite.addTest(makeSuite(TestSubdomainLanguageNegotiation))
    return suite
