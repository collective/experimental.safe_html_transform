import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase

from Products.ATContentTypes.tests.utils import dcEdit
from Products.ATContentTypes.content.folder import ATFolder
from Products.ATContentTypes.content.folder import ATBTreeFolder
from OFS.interfaces import IOrderedContainer as IOrderedContainer
from Products.ATContentTypes.interfaces import IATFolder
from Products.ATContentTypes.interfaces import IATBTreeFolder

from zope.interface.verify import verifyObject
from Products.ATContentTypes.interfaces import ISelectableConstrainTypes


def editATCT(obj):
    dcEdit(obj)

tests = []


class FolderTestMixin:
    """Contains some general tests for both ATFolder and ATBTreeFolder
    """
    def test_implementsConstrainTypes(self):
        self.assertTrue(ISelectableConstrainTypes.providedBy(self._ATCT))
        self.assertTrue(verifyObject(ISelectableConstrainTypes, self._ATCT))


class TestSiteATFolder(atcttestcase.ATCTTypeTestCase, FolderTestMixin):

    klass = ATFolder
    portal_type = 'Folder'
    title = 'Folder'
    meta_type = 'ATFolder'

    def test_implementsOrderInterface(self):
        self.assertTrue(IOrderedContainer.providedBy(self._ATCT))
        self.assertTrue(verifyObject(IOrderedContainer, self._ATCT))

    def test_implementsATFolder(self):
        iface = IATFolder
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsConstrainTypes(self):
        iface = ISelectableConstrainTypes
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)

    def test_get_size(self):
        atct = self._ATCT
        self.assertEqual(atct.get_size(), 1)

    def test_schema_marshall(self):
        pass

tests.append(TestSiteATFolder)


class TestSiteATBTreeFolder(atcttestcase.ATCTTypeTestCase, FolderTestMixin):

    klass = ATBTreeFolder
    portal_type = 'Large Plone Folder'
    title = 'Large Folder'
    meta_type = 'ATBTreeFolder'

    def test_implementsATBTreeFolder(self):
        iface = IATBTreeFolder
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsConstrainTypes(self):
        iface = ISelectableConstrainTypes
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_isOrdered(self):
        self.assertTrue(IOrderedContainer.providedBy(self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)
        self.assertTrue('Test title' == new.Title())
        self.assertTrue('Test description' == new.Description())

    def test_get_size(self):
        atct = self._ATCT
        self.assertEqual(atct.get_size(), 1)

    def test_schema_marshall(self):
        pass

    def test_dictBehavior(self):
        # this test currently fails intentionally (see
        # http://dev.plone.org/collective/changeset/53298).
        # debugging it for a while shows that BTreeFolders don't
        # work as iterators for some strange reason.  while
        # "list(folder.__iter__())" works just fine, "list(folder)"
        # doesn't.  python doesn't seem to recognize the `__iter__`
        # method and instead falls back to its standard iterator
        # cycling the list via `__len__` and `__getitem__`.  however,
        # the interesting bit here is, that "list(folder.aq_base)"
        # does work, so apparently it's acquisition biting us here...
        #
        # meanwhile this bug has been fixed upstream in Zope (see
        # http://svn.zope.org/?rev=94907&view=rev), so the next release
        # should make this test pass
        #
        # update: using zope 2.10.8 makes this test pass indeed...
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Folder', 'f1')
        f1 = self.portal['f1']

        from Products.ATContentTypes.content.document import ATDocument
        new_doc = ATDocument('d1')
        f1['d1'] = new_doc
        new_doc = f1['d1']  # aq-wrap

        self.assertEqual(['d1'], list(f1.keys()))  # keys
        self.assertEqual(['d1'], list(f1.iterkeys()))  # iterkeys
        try:
            self.assertEqual(['d1'], list(f1))  # iter
        except (KeyError, AttributeError):
            print '\nKnown failure: please see comments in `test_dictBehavior`!'
        self.assertEqual(['d1'], list(f1.aq_base))  # iter (this works, weird!)
        self.assertTrue(f1.values()[0].aq_base is new_doc.aq_base)  # values
        self.assertTrue(f1.get('d1').aq_base is new_doc.aq_base)  # get
        self.assertTrue('d1' in f1)  # contains


tests.append(TestSiteATBTreeFolder)


class TestATFolderFields(atcttestcase.ATCTFieldTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATFolder)

    def test_field_enableConstrainMixin(self):
        pass
        #self.fail('not implemented')

    def test_field_locallyAllowedTypes(self):
        pass
        #self.fail('not implemented')

tests.append(TestATFolderFields)


class TestATBTreeFolderFields(TestATFolderFields):

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATBTreeFolder)

tests.append(TestATBTreeFolderFields)


class TestATFolderFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'Folder'
    views = ('folder_listing', 'atct_album_view', )

    def test_dynamic_view_without_view(self):
        # dynamic view mixin should work
        response = self.publish('%s/' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)

    def test_selectViewTemplate(self):
        # create an object using the createObject script
        self.publish(self.obj_path +
                     '/selectViewTemplate?templateId=atct_album_view',
                     self.owner_auth)
        self.assertEqual(self.obj.getLayout(), 'atct_album_view')

tests.append(TestATFolderFunctional)


class TestATBTreeFolderFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'Large Plone Folder'
    views = ('folder_listing', 'atct_album_view', )

    def test_templatemixin_view_without_view(self):
        # template mixin magic should work
        response = self.publish('%s/' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)

tests.append(TestATBTreeFolderFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
