import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.

from Products.ATContentTypes.tests import atcttestcase
from Products.ATContentTypes.config import TOOLNAME
from Products.ATContentTypes.config import SWALLOW_IMAGE_RESIZE_EXCEPTIONS
from Products.ATContentTypes.tool.atct import ATCTTool
from Products.CMFCore.utils import getToolByName

tests = []


class TestInstallation(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal.aq_explicit, TOOLNAME)
        self.ttool = getattr(self.portal.aq_explicit, 'portal_types')
        self.cat = getattr(self.portal.aq_explicit, 'portal_catalog')

    def test_tool_installed(self):
        t = getToolByName(self.portal, TOOLNAME, None)
        self.assertTrue(t, t)
        self.assertTrue(isinstance(t, ATCTTool), t.__class__)
        self.assertEqual(t.meta_type, 'ATCT Tool')
        self.assertEqual(t.getId(), TOOLNAME)

    def test_skin_installed(self):
        stool = getattr(self.portal.aq_explicit, 'portal_skins')
        self.assertTrue('ATContentTypes' in stool)

    def test_installedAllTypes(self):
        # test that all types are installed well
        ids = ('Document', 'File', 'Folder', 'Image', 'Link',
            'News Item', 'Topic', 'Event')
        for i in ids:
            self.assertTrue(i in self.ttool)

    def test_not_quickinstalled(self):
        qi = getattr(self.portal, 'portal_quickinstaller')
        products = [prod['id'] for prod in qi.listInstalledProducts()]
        self.assertFalse('ATContentTypes' in products)

    def test_release_settings_SAVE_TO_FAIL_FOR_DEVELOPMENT(self):
        self.assertEqual(SWALLOW_IMAGE_RESIZE_EXCEPTIONS, True)

    def test_reindex_doesnt_add_tools(self):
        cat = self.cat
        ids = [i for i in self.portal if i.startswith('portal_')]
        # a rought guess
        self.assertFalse(len(ids) < 5)
        for id in ids:
                result = cat(id=id)
                l = len(result)
                self.assertEqual(l, 0, (id, l, result))

    def test_adds_related_items_catalog_index(self):
        self.assertEqual(self.cat.Indexes['getRawRelatedItems'].__class__.__name__,
                         'KeywordIndex')

    def test_api_import(self):
        import Products.ATContentTypes.atct


tests.append(TestInstallation)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
