import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.ATContentTypes import permission
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault as ZopeTwoISelectableBrowserDefault
from Products.CMFDynamicViewFTI.interface import ISelectableBrowserDefault

tests = []


# XXX: This should probably move to the new CMFDynamicViewFTI
class TestBrowserDefaultMixin(atcttestcase.ATCTSiteTestCase):
    folder_type = 'Folder'
    image_type = 'Image'
    document_type = 'Document'
    file_type = 'File'

    def afterSetUp(self):
        atcttestcase.ATCTSiteTestCase.afterSetUp(self)
        self.folder.invokeFactory(self.folder_type, id='af')
        # an ATCT folder
        self.af = self.folder.af
        # Needed because getFolderContents needs to clone the REQUEST
        self.app.REQUEST.set('PARENTS', [self.app])

    def test_isMixedIn(self):
        self.assertTrue(isinstance(self.af, BrowserDefaultMixin),
                        "ISelectableBrowserDefault was not mixed in to ATFolder")
        self.assertTrue(ZopeTwoISelectableBrowserDefault.providedBy(self.af),
                        "ISelectableBrowserDefault not implemented by ATFolder instance")
        self.assertTrue(ISelectableBrowserDefault.providedBy(self.af),
                        "ISelectableBrowserDefault not implemented by ATFolder instance")

    def test_defaultFolderViews(self):
        self.assertEqual(self.af.getLayout(), 'folder_listing')
        self.assertEqual(self.af.getDefaultPage(), None)
        self.assertEqual(self.af.defaultView(), 'folder_listing')
        self.assertEqual(self.af.getDefaultLayout(), 'folder_listing')
        layoutKeys = [v[0] for v in self.af.getAvailableLayouts()]
        self.assertTrue('folder_listing' in layoutKeys)
        self.assertTrue('atct_album_view' in layoutKeys)

        resolved = self.af.unrestrictedTraverse('folder_listing')()
        browserDefault = self.af.__browser_default__(None)[1][0]
        browserDefaultResolved = self.af.unrestrictedTraverse(browserDefault)()
        self.assertEqual(resolved, browserDefaultResolved)

    def test_canSetLayout(self):
        self.assertTrue(self.af.canSetLayout())
        self.af.invokeFactory('Document', 'ad')
        self.portal.manage_permission(permission.ModifyViewTemplate, [], 0)
        self.assertFalse(self.af.canSetLayout())  # Not permitted

    def test_setLayout(self):
        self.af.setLayout('atct_album_view')
        self.assertEqual(self.af.getLayout(), 'atct_album_view')
        self.assertEqual(self.af.getDefaultPage(), None)
        self.assertEqual(self.af.defaultView(), 'atct_album_view')
        self.assertEqual(self.af.getDefaultLayout(), 'folder_listing')
        layoutKeys = [v[0] for v in self.af.getAvailableLayouts()]
        self.assertTrue('folder_listing' in layoutKeys)
        self.assertTrue('atct_album_view' in layoutKeys)

        resolved = self.af.unrestrictedTraverse('atct_album_view')()
        browserDefault = self.af.__browser_default__(None)[1][0]
        browserDefaultResolved = self.af.unrestrictedTraverse(browserDefault)()
        self.assertEqual(resolved, browserDefaultResolved)

    def test_canSetDefaultPage(self):
        self.assertTrue(self.af.canSetDefaultPage())
        self.af.invokeFactory('Document', 'ad')
        self.assertFalse(self.af.ad.canSetDefaultPage())  # Not folderish
        self.portal.manage_permission(permission.ModifyViewTemplate, [], 0)
        self.assertFalse(self.af.canSetDefaultPage())  # Not permitted

    def test_setDefaultPage(self):
        self.af.invokeFactory('Document', 'ad')
        self.af.setDefaultPage('ad')
        self.assertEqual(self.af.getDefaultPage(), 'ad')
        self.assertEqual(self.af.defaultView(), 'ad')
        self.assertEqual(self.af.__browser_default__(None), (self.af, ['ad']))

        # still have layout settings
        self.assertEqual(self.af.getLayout(), 'folder_listing')
        self.assertEqual(self.af.getDefaultLayout(), 'folder_listing')
        layoutKeys = [v[0] for v in self.af.getAvailableLayouts()]
        self.assertTrue('folder_listing' in layoutKeys)
        self.assertTrue('atct_album_view' in layoutKeys)

    def test_setDefaultPageUpdatesCatalog(self):
        # Ensure that Default page changes update the catalog
        cat = self.portal.portal_catalog
        self.af.invokeFactory('Document', 'ad')
        self.af.invokeFactory('Document', 'other')
        self.assertEqual(len(cat(getId=['ad', 'other'], is_default_page=True)), 0)
        self.af.setDefaultPage('ad')
        self.assertEqual(len(cat(getId='ad', is_default_page=True)), 1)
        self.af.setDefaultPage('other')
        self.assertEqual(len(cat(getId='other', is_default_page=True)), 1)
        self.assertEqual(len(cat(getId='ad', is_default_page=True)), 0)
        self.af.setDefaultPage(None)
        self.assertEqual(len(cat(getId=['ad', 'other'], is_default_page=True)), 0)

    def test_setLayoutUnsetsDefaultPage(self):
        layout = 'atct_album_view'
        self.af.invokeFactory('Document', 'ad')
        self.af.setDefaultPage('ad')
        self.assertEqual(self.af.getDefaultPage(), 'ad')
        self.assertEqual(self.af.defaultView(), 'ad')
        self.af.setLayout(layout)
        self.assertEqual(self.af.getDefaultPage(), None)
        self.assertEqual(self.af.defaultView(), layout)
        resolved = self.af.unrestrictedTraverse(layout)()
        browserDefault = self.af.__browser_default__(None)[1][0]
        browserDefaultResolved = self.af.unrestrictedTraverse(browserDefault)()
        self.assertEqual(resolved, browserDefaultResolved)

    def test_inherit_parent_layout(self):
        # Check to see if subobjects of the same type inherit the layout set
        # on the parent object
        af = self.af
        af.setLayout('folder_tabular_view')
        af.invokeFactory('Folder', 'subfolder', title='folder 2')
        subfolder = af.subfolder
        self.assertEqual(subfolder.getLayout(), 'folder_tabular_view')

    def test_inherit_parent_layout_if_different_type(self):
        # Objects will not inherit the layout if parent object is a different
        # type
        af = self.af
        af.setLayout('folder_tabular_view')
        # Create a subobject of a different type
        af.invokeFactory('Document', 'page', title='page')
        page = af.page
        self.assertFalse(page.getLayout() == 'folder_tabular_view')

tests.append(TestBrowserDefaultMixin)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
