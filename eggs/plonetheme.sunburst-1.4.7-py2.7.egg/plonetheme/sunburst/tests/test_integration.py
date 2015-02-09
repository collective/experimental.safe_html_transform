from plonetheme.sunburst.tests.base import SunburstTestCase as TestCase


class SunburstTestCase(TestCase):

    def test_sunburst_layers_available(self):
        self.assertTrue('sunburst_images' in self.portal.portal_skins)
        self.assertTrue('sunburst_styles' in self.portal.portal_skins)
        self.assertTrue('sunburst_templates' in self.portal.portal_skins)

    def test_sunburst_skin_installed(self):
        self.skins = self.portal.portal_skins
        theme = self.skins.getDefaultSkin()
        self.assertTrue(theme == 'Sunburst Theme', 'Default theme is %s' % theme)


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
