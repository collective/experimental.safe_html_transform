# This test confirms that views assigned to theme-specific layers
# take precedence over views assigned to other kinds of layers.

from Products.CMFPlone.tests import PloneTestCase
from zope.publisher.browser import TestRequest

from zope.event import notify
from zope.interface import Interface, directlyProvides, directlyProvidedBy
from zope.component import getGlobalSiteManager
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.browser import setDefaultSkin
from zope.traversing.interfaces import BeforeTraverseEvent
from plone.theme.interfaces import IDefaultPloneLayer


class IThemeSpecific(IDefaultPloneLayer):
    pass


class IAdditiveLayer(Interface):
    pass


class IAdditiveLayerExtendingDefault(IDefaultPloneLayer):
    pass


class LayerPrecedenceTestCase(PloneTestCase.FunctionalTestCase):

    additive_layer = None
    theme_layer = None

    def afterSetUp(self):
        gsm = getGlobalSiteManager()
        if self.theme_layer is not None:
            self._skin_name = self.portal.portal_skins.getDefaultSkin()
            self._old_theme_layer = gsm.queryUtility(IBrowserSkinType,
                                                     name=self._skin_name)
            gsm.registerUtility(self.theme_layer,
                                IBrowserSkinType,
                                self._skin_name)

    def _get_request_interfaces(self):
        request = TestRequest()
        setDefaultSkin(request)
        orig_iro = list(directlyProvidedBy(request).__iro__)
        directlyProvides(request, [self.additive_layer] + orig_iro)
        notify(BeforeTraverseEvent(self.portal, request))
        iro = list(request.__provides__.__iro__)
        return iro

    def testLayerPrecedence(self):
        iro = self._get_request_interfaces()
        if self.theme_layer is not None:
            theme_layer_pos = iro.index(self.theme_layer)
            plone_default_pos = iro.index(IDefaultPloneLayer)
        additive_layer_pos = iro.index(self.additive_layer)
        zope_default_pos = iro.index(IDefaultBrowserLayer)

        # We want to have the theme layer first, followed by additive layers,
        # followed by default layers.
        if self.theme_layer is not None:
            self.assertEqual(theme_layer_pos, 0)
            self.assertTrue(theme_layer_pos < additive_layer_pos)
            # for BBB, IDefaultPloneLayer and ICMFDefaultSkin are not present
            # unless there are theme layers which extend them.
            self.assertTrue(additive_layer_pos < plone_default_pos)
        self.assertTrue(additive_layer_pos < zope_default_pos)

    def beforeTearDown(self):
        gsm = getGlobalSiteManager()
        if self.theme_layer is not None:
            res = gsm.unregisterUtility(provided=IBrowserSkinType,
                                        name=self._skin_name)
            self.assertTrue(res)
            if self._old_theme_layer is not None:
                gsm.registerUtility(self._old_theme_layer,
                                    IBrowserSkinType,
                                    self._skin_name)


class TestPrecedenceWithAdditiveLayerExtendingInterface(LayerPrecedenceTestCase):
    theme_layer = IThemeSpecific
    additive_layer = IAdditiveLayer


class TestPrecedenceWithAdditiveLayerExtendingDefault(LayerPrecedenceTestCase):
    theme_layer = IThemeSpecific
    additive_layer = IAdditiveLayerExtendingDefault


class TestPrecedenceWithNoThemeLayer(LayerPrecedenceTestCase):
    theme_layer = None
    additive_layer = IAdditiveLayer


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPrecedenceWithAdditiveLayerExtendingInterface))
    suite.addTest(makeSuite(TestPrecedenceWithAdditiveLayerExtendingDefault))
    suite.addTest(makeSuite(TestPrecedenceWithNoThemeLayer))
    return suite
