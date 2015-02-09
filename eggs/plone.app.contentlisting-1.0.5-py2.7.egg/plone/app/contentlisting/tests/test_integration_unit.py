from Products.CMFCore.utils import getToolByName
from zope.interface.verify import verifyObject

from .base import ContentlistingFunctionalTestCase
from ..interfaces import IContentListing
from ..interfaces import IContentListingObject


class TestSetup(ContentlistingFunctionalTestCase):

    def setUp(self):
        super(TestSetup, self).setUp()
        self.workflow = getToolByName(self.portal, 'portal_workflow')
        self.catalog = getToolByName(self.portal, 'portal_catalog')

    def test_able_to_add_document(self):
        # just a dummy test to see that the basics are running
        new_id = self.folder.invokeFactory('Document', 'mypage')
        self.assertEquals('mypage', new_id)

    def test_simple_contentlisting(self):
        results = []
        listing = IContentListing(results)
        from plone.app.contentlisting.contentlisting import ContentListing
        self.failUnless(isinstance(listing, ContentListing))

    def test_making_contentlisting(self):
        results = self.catalog()
        listing = IContentListing(results)
        from plone.app.contentlisting.contentlisting import ContentListing
        self.failUnless(isinstance(listing, ContentListing))

    def test_making_contentlistingobjects(self):
        results = self.catalog()
        listing = IContentListing(results)
        from plone.app.contentlisting.catalog import \
            CatalogContentListingObject
        self.failUnless(isinstance(listing[0], CatalogContentListingObject))

    def test_listing_interface(self):
        self.failUnless(verifyObject(IContentListing,
                                     IContentListing(self.catalog())))

    def test_listing_object_interface(self):
        self.failUnless(verifyObject(IContentListingObject,
                                     IContentListing(self.catalog())[0]))


class TestIndividualCatalogContentItems(ContentlistingFunctionalTestCase):

    def setUp(self):
        super(TestIndividualCatalogContentItems, self).setUp()
        self.folder.invokeFactory(
            'Document', 'mypage', title='My Page', description='blah')
        self.item = self.folder.restrictedTraverse('@@folderListing')()[0]
        self.realitem = self.folder.mypage

    def test_printing_item(self):
        self.assertEqual(repr(self.item),
            '<plone.app.contentlisting.catalog.CatalogContentListingObject '
            'instance at /plone/test-folder/mypage>')
        self.assertEqual(str(self.item),
            '<plone.app.contentlisting.catalog.CatalogContentListingObject '
            'instance at /plone/test-folder/mypage>')

    def test_special_getattr_with_underscore(self):
        # looking up attributes starting with _ should always raise
        # AttributeError
        self.assertRaises(AttributeError, self.item.__getattr__, 'foo')

    def test_special_getattr_from_brain(self):
        # Asking for an attribute not in the contentlistingobject, should
        # defer lookup to the brain
        self.assertEqual(self.item.is_folderish, False)
        self.failUnless(repr(self.item.getDataOrigin())[:35],
            '<Products.ZCatalog.Catalog.mybrains')

    def test_special_getattr_from_object(self):
        # Asking for an attribute not in the contentlistingobject, should
        # defer lookup to the brain"""
        self.assertEqual(self.item.absolute_url(), '')
        self.assertEqual(repr(self.item.getDataOrigin()),
            '<ATDocument at /plone/test-folder/mypage>')

    def test_item_Title(self):
        self.assertEqual(self.item.Title(), 'My Page')
        self.assertEqual(self.item.Title(), self.realitem.Title())

    def test_item_Description(self):
        self.assertEqual(self.item.Description(), 'blah')
        self.assertEqual(self.item.Description(), self.realitem.Description())

    def test_item_Creator(self):
        self.assertEqual(self.item.Creator(), 'test_user_1_')

    def test_item_getURL(self):
        self.assertEqual(self.item.getURL(),
            'http://nohost/plone/test-folder/mypage')
        self.assertEqual(self.item.getURL(), self.realitem.absolute_url())

    def test_item_getIcon(self):
        # since icons were changed to css sprites for most types for Plone 4,
        # this one needs to use an image for the test.
        self.folder.invokeFactory(
            'Image', 'myimage', title='My Image', description='blah')
        self.item = self.folder.restrictedTraverse('@@folderListing')()[1]
        self.assertEqual(self.item.getIcon(),
            u'<img width="16" height="16" src="http://nohost/plone/png.png" '
            u'alt="Image" />')

    def test_item_getSize(self):
        self.assertEqual(self.item.getSize().upper(), '0 KB')

    def test_item_reviewState(self):
        wftool = getToolByName(self.realitem, "portal_workflow")
        wf = wftool.getInfoFor(self.realitem, 'review_state')
        self.assertEqual(self.item.review_state(), wf)

    def test_item_Type(self):
        self.assertEqual(self.item.Type(), u'Page')
        self.assertEqual(self.item.Type().domain, u'plone')

    def test_appendViewAction(self):
        # checking that we append the view action to urls when needed
        self.assertEqual(self.item.appendViewAction(), '')
        self.folder.invokeFactory(
            'Image', 'myimage', title='My Image', description='blah')
        self.item = self.folder.restrictedTraverse('@@folderListing')()[1]
        self.assertEqual(self.item.appendViewAction(), '/view')

    def test_item_ContentTypeClass(self):
        # checking the that we print nice strings for css class identifiers
        self.assertEqual(self.item.ContentTypeClass(), 'contenttype-document')

    def test_item_Language(self):
        self.assertEqual(self.item.Language(), 'en')

    def test_comparision(self):
        self.assertEqual(IContentListingObject(self.folder.mypage), self.item)

    def test_containment(self):
        # we can test containment for normal content objects against
        # contentlistings
        self.failUnless(self.folder.mypage in
                        self.folder.restrictedTraverse('@@folderListing')())


class TestIndividualRealContentItems(ContentlistingFunctionalTestCase):

    def setUp(self):
        super(TestIndividualRealContentItems, self).setUp()
        self.folder.invokeFactory(
            'Document', 'mypage', title='My Page', description='blah')
        self.item = IContentListingObject(self.folder.mypage)
        self.realitem = self.folder.mypage

    def test_printing_item(self):
        self.assertEqual(repr(self.item),
            '<plone.app.contentlisting.realobject.RealContentListingObject '
            'instance at /plone/test-folder/mypage>')
        self.assertEqual(str(self.item),
            '<plone.app.contentlisting.realobject.RealContentListingObject '
            'instance at /plone/test-folder/mypage>')

    def test_special_getattr_with_underscore(self):
        # looking up attributes starting with _ should always raise
        # AttributeError
        self.assertRaises(AttributeError, self.item.__getattr__, 'foo')

    def test_special_getattr_from_object(self):
        # Asking for an attribute not in the contentlistingobject, should
        # defer lookup to the brain
        self.assertEqual(self.item.absolute_url(), '')
        self.assertEqual(repr(self.item.getDataOrigin()),
            '<ATDocument at /plone/test-folder/mypage>')

    def test_item_Title(self):
        self.assertEqual(self.item.Title(), 'My Page')
        self.assertEqual(self.item.Title(), self.realitem.Title())

    def test_item_Description(self):
        self.assertEqual(self.item.Description(), 'blah')
        self.assertEqual(self.item.Description(), self.realitem.Description())

    def test_item_Creator(self):
        self.assertEqual(self.item.Creator(), 'test_user_1_')

    def test_item_getURL(self):
        self.assertEqual(self.item.getURL(),
            'http://nohost/plone/test-folder/mypage')
        self.assertEqual(self.item.getURL(), self.realitem.absolute_url())

    def test_item_getIcon(self):
        # since icons were changed to css sprites for most types for Plone 4,
        # this one needs to use an image for the test.
        self.folder.invokeFactory(
            'Image', 'myimage', title='My Image', description='blah')
        self.item = IContentListingObject(self.folder.myimage)
        self.assertEqual(self.item.getIcon(),
            u'<img width="16" height="16" src="http://nohost/plone/png.png" '
            u'alt="Image" />')

    def test_item_reviewState(self):
        wftool = getToolByName(self.realitem, "portal_workflow")
        wf = wftool.getInfoFor(self.realitem, 'review_state')
        self.assertEqual(self.item.review_state(), wf)

    def test_item_Type(self):
        self.assertEqual(self.item.Type(), u'Page')
        self.assertEqual(self.item.Type().domain, u'plone')

    def test_item_ContentTypeClass(self):
        # checking the that we print nice strings for css class identifiers
        self.assertEqual(self.item.ContentTypeClass(), 'contenttype-document')

    def test_item_Language(self):
        self.assertEqual(self.item.Language(), 'en')

    def test_item_uuid(self):
        uuid = self.item.uuid()
        assert uuid
        assert uuid != self.item.getPath()


class TestFolderContents(ContentlistingFunctionalTestCase):
    """Testing that the folder contents browserview works and behaves
    as it should.
    """

    def test_empty_folder_contents(self):
        folderlisting = self.folder.restrictedTraverse('@@folderListing')()
        self.assertEqual(len(folderlisting), 0)
        self.assertEqual(folderlisting.actual_result_count, 0)

    def test_item_in_folder_contents(self):
        # adding a new page, adds to the length of folder contents
        self.folder.invokeFactory('Document', 'mypage')
        folderlisting = self.folder.restrictedTraverse('@@folderListing')()
        self.assertEqual(len(folderlisting), 1)
        self.assertEqual(folderlisting.actual_result_count, 1)

    def test_folder_contents(self):
        # call the generic folder contents browserview. Check that it makes
        # the results a contentlisting, regardless of batching
        self.folder.invokeFactory('Document', 'mypage')
        folderlisting = self.folder.restrictedTraverse('@@folderListing')()
        self.failUnless(verifyObject(IContentListing, folderlisting))

    def test_batching_folder_contents(self):
        # call the generic folder contents browserview. Check that it makes
        # the results a contentlisting, regardless of batching
        self.folder.invokeFactory('Document', 'mypage')
        folderlisting = self.folder.restrictedTraverse('@@folderListing')(
            batch=True, b_size=1)
        self.failUnless(verifyObject(IContentListing, folderlisting))
        self.assertEqual(len(folderlisting), 1)

    def test_batching_folder_contents_2(self):
        # call the generic folder contents browserview. Check that it makes
        # the results a contentlisting, regardless of batching
        new_id = self.folder.invokeFactory('Document', 'mypage')
        new_id2 = self.folder.invokeFactory('Document', 'mypage2')
        folderlisting = self.folder.restrictedTraverse('@@folderListing')(
            batch=True, b_size=1)
        self.failUnless(folderlisting[0].getId() == new_id)
        self.assertEqual(len(folderlisting), 1)
        self.assertEqual(folderlisting.actual_result_count, 2)

        folderlisting = self.folder.restrictedTraverse('@@folderListing')(
            batch=True, b_size=1, b_start=1)
        self.assertEqual(folderlisting[0].getId(), new_id2)
        self.assertEqual(len(folderlisting), 1)
        self.assertEqual(folderlisting.actual_result_count, 2)


def test_suite():
    import unittest2 as unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSetup))
    suite.addTest(unittest.makeSuite(TestIndividualCatalogContentItems))
    suite.addTest(unittest.makeSuite(TestIndividualRealContentItems))
    suite.addTest(unittest.makeSuite(TestFolderContents))
    return suite
