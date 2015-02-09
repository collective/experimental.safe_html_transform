import unittest
from plone.app.openid.tests.base import OpenIdTestCase
from Products.PluggableAuthService.interfaces.plugins \
        import IExtractionPlugin, ILoginPasswordExtractionPlugin

class TestOpenIdView(OpenIdTestCase):
    def test_DefaultConfig(self):
        pas_info=self.pas_info
        self.assertEquals(pas_info.hasOpenIDExtractor(), False)
        self.assertEquals(pas_info.hasLoginPasswordExtractor(), True)

    def test_OpenIdInstalled(self):
        self.portal.portal_setup.runAllImportStepsFromProfile(
            'profile-plone.app.openid:default')
        pas_info=self.pas_info
        self.assertEquals(pas_info.hasOpenIDExtractor(), True)
        self.assertEquals(pas_info.hasLoginPasswordExtractor(), True)

    def testOnlyOpenIdInstalled(self):
        plugins=self.pas.plugins.listPlugins(IExtractionPlugin)
        for (id, plugin) in plugins:
            if ILoginPasswordExtractionPlugin.providedBy(plugin):
                plugin.manage_activateInterfaces(interfaces=())
        self.portal.portal_setup.runAllImportStepsFromProfile(
            'profile-plone.app.openid:default')

        pas_info=self.pas_info
        self.assertEquals(pas_info.hasOpenIDExtractor(), True)
        self.assertEquals(pas_info.hasLoginPasswordExtractor(), False)


def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenIdView))
    return suite

