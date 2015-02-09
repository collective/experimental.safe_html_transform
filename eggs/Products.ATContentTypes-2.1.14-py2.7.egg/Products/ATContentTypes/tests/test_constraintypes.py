import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase

from AccessControl.SecurityManagement import newSecurityManager

from Products.ATContentTypes.lib import constraintypes
from Products.CMFPlone.interfaces import ISelectableConstrainTypes

tests = []


class TestConstrainTypes(atcttestcase.ATCTSiteTestCase):
    folder_type = 'Folder'
    image_type = 'Image'
    document_type = 'Document'
    file_type = 'File'

    def afterSetUp(self):
        atcttestcase.ATCTSiteTestCase.afterSetUp(self)
        self.folder.invokeFactory(self.folder_type, id='af')
        self.tt = self.portal.portal_types
        # an ATCT folder
        self.af = self.folder.af
        # portal_types object for ATCT folder
        self.at = self.tt.getTypeInfo(self.af)

    def test_isMixedIn(self):
        self.assertTrue(isinstance(self.af,
                                   constraintypes.ConstrainTypesMixin),
                        "ConstrainTypesMixin was not mixed in to ATFolder")
        self.assertTrue(ISelectableConstrainTypes.providedBy(self.af),
                        "ISelectableConstrainTypes not implemented by ATFolder instance")

    def test_enabled(self):
        self.af.setConstrainTypesMode(constraintypes.ENABLED)
        self.af.setLocallyAllowedTypes(['Folder', 'Image'])
        self.af.setImmediatelyAddableTypes(['Folder'])

        self.assertEqual(self.af.getLocallyAllowedTypes(),
                                ('Folder', 'Image',))
        self.assertEqual(self.af.getImmediatelyAddableTypes(),
                                ('Folder',))

        self.assertRaises(ValueError, self.af.invokeFactory, 'Document', 'a')
        try:
            self.af.invokeFactory('Image', 'image', title="death")
        except ValueError:
            self.fail()

    def test_disabled(self):
        self.af.setConstrainTypesMode(constraintypes.DISABLED)
        self.af.setLocallyAllowedTypes(['Folder', 'Image'])
        self.af.setImmediatelyAddableTypes(['Folder'])

        # We can still set and persist, even though it is disabled - must
        # remember!
        self.assertEqual(self.af.getRawLocallyAllowedTypes(),
                                ('Folder', 'Image',))
        self.assertEqual(self.af.getRawImmediatelyAddableTypes(),
                                ('Folder',))

        try:
            self.af.invokeFactory('Document', 'whatever', title='life')
            self.af.invokeFactory('Image', 'image', title="more life")
        except ValueError:
            self.fail()

        # Make sure immediately-addable are all types if we are disabled
        allowedIds = [ctype.getId() for ctype in self.af.allowedContentTypes()]
        self.assertEqual(allowedIds, self.af.getImmediatelyAddableTypes())

    def test_acquireFromHomogenousParent(self):
        # Set up outer folder with restrictions enabled
        self.af.setConstrainTypesMode(constraintypes.ENABLED)
        self.af.setLocallyAllowedTypes(['Folder', 'Image'])
        self.af.setImmediatelyAddableTypes(['Folder'])

        # Create inner type to acquire (default)
        self.af.invokeFactory('Folder', 'inner', title='inner')
        inner = self.af.inner

        inner.setConstrainTypesMode(constraintypes.ACQUIRE)

        # Test persistence
        inner.setLocallyAllowedTypes(['Document', 'Event'])
        inner.setImmediatelyAddableTypes(['Document'])

        self.assertEqual(inner.getRawLocallyAllowedTypes(),
                                ('Document', 'Event',))
        self.assertEqual(inner.getRawImmediatelyAddableTypes(),
                                ('Document',))

        self.assertRaises(ValueError, inner.invokeFactory, 'Event', 'a')
        try:
            inner.invokeFactory('Image', 'whatever', title='life')
        except ValueError:
            self.fail()

        # Make sure immediately-addable are inherited
        self.assertEqual(inner.getImmediatelyAddableTypes(),
                         self.af.getImmediatelyAddableTypes())

        # Create a new unprivileged user who can only access the inner folder
        self.portal.acl_users._doAddUser('restricted', 'secret', ['Member'], [])
        inner.manage_addLocalRoles('restricted', ('Manager',))
        # Login the new user
        user = self.portal.acl_users.getUserById('restricted')
        newSecurityManager(None, user)
        self.assertEqual(inner.getLocallyAllowedTypes(),
                        ('Folder', 'Image'))

    def test_acquireFromHetereogenousParent(self):

        # Let folder use a restricted set of types
        self.portal.portal_types.Folder.filter_content_types = 1
        self.portal.portal_types.Folder.allowed_content_types = \
            ('Document', 'Image', 'News Item', 'Topic', 'Folder')

        # Set up outer folder with restrictions enabled
        self.af.setConstrainTypesMode(constraintypes.ENABLED)
        self.af.setLocallyAllowedTypes(['Folder', 'Image'])
        self.af.setImmediatelyAddableTypes(['Folder', 'Image'])

        # Create inner type to acquire (default)
        self.af.invokeFactory('Folder', 'outer', title='outer')
        outer = self.af.outer

        outer.invokeFactory('Folder', 'inner', title='inner')
        inner = outer.inner

        inner.setConstrainTypesMode(constraintypes.ACQUIRE)

        # Test persistence
        inner.setLocallyAllowedTypes(['Document', 'Event'])
        inner.setImmediatelyAddableTypes(['Document'])

        self.assertEqual(inner.getRawLocallyAllowedTypes(),
                                ('Document', 'Event',))
        self.assertEqual(inner.getRawImmediatelyAddableTypes(),
                                ('Document',))

        # Fail - we didn't acquire this, really, since we can't acquire
        # from parent folder of different type
        self.assertRaises(ValueError, inner.invokeFactory, 'Topic', 'a')
        self.assertFalse('News Item' in inner.getLocallyAllowedTypes())

        # Make sure immediately-addable are set to default
        self.assertEqual(inner.getImmediatelyAddableTypes(),
                         inner.getLocallyAllowedTypes())
        self.assertEqual(inner.allowedContentTypes(), outer.allowedContentTypes())

        # Login the new user
        self.portal.acl_users._doAddUser('restricted', 'secret', ['Member'], [])
        inner.manage_addLocalRoles('restricted', ('Manager',))
        user = self.portal.acl_users.getUserById('restricted')
        newSecurityManager(None, user)
        self.assertEqual([t.getId() for t in inner.allowedContentTypes()],
                             ['Folder', 'Image'])


    def test_acquireFromCustomHetereogenousParentWithConstraint(self):
        self.loginAsPortalOwner()
        cp = self.portal.portal_types.manage_copyObjects(['Folder'])
        self.portal.portal_types.manage_pasteObjects(cp)
        self.portal.portal_types.manage_renameObject('copy_of_Folder', 'Folder2')

        # Let folder use a restricted set of types
        self.portal.portal_types.Folder.filter_content_types = 1
        self.portal.portal_types.Folder.allowed_content_types = \
            ('Document', 'Image', 'News Item', 'Topic', 'Folder', 'Folder2')

        self.portal.portal_types.Folder2.filter_content_types = 1
        self.portal.portal_types.Folder2.allowed_content_types = \
            ('Document', 'Image', 'Topic', 'Folder')

        # Set up outer folder with restrictions enabled
        self.af.setConstrainTypesMode(constraintypes.ENABLED)
        self.af.setLocallyAllowedTypes(['Folder2', 'Image', 'News Item'])
        self.af.setImmediatelyAddableTypes(['Folder2', 'Image'])

        # Create type to acquire
        self.af.invokeFactory('Folder2', 'folder2', title='folder2')
        folder2 = self.af.folder2
        folder2.setConstrainTypesMode(constraintypes.ACQUIRE)

        # News item is not in addable types because it is globally forbidden in Folder2 type
        # and Folder is not in addable types because it is locally forbidden in folder2 parent
        self.assertEqual([fti.getId() for fti in folder2.allowedContentTypes()],
                             ['Image'])
        self.assertEqual(folder2.getImmediatelyAddableTypes(), ['Image'])

        # Login the new user
        self.portal.acl_users._doAddUser('restricted', 'secret', ['Member'], [])
        folder2.manage_addLocalRoles('restricted', ('Manager',))
        user = self.portal.acl_users.getUserById('restricted')
        newSecurityManager(None, user)
        self.assertEqual([t.getId() for t in self.af.allowedContentTypes()],
                             [])
        self.assertEqual([t.getId() for t in folder2.allowedContentTypes()],
                             ['Image'])


    def test_acquireFromCustomHetereogenousParentWithoutConstraint(self):
        self.loginAsPortalOwner()
        cp = self.portal.portal_types.manage_copyObjects(['Folder'])
        self.portal.portal_types.manage_pasteObjects(cp)
        self.portal.portal_types.manage_renameObject('copy_of_Folder', 'Folder2')

        # Let folder use a restricted set of types
        self.portal.portal_types.Folder.filter_content_types = 1
        self.portal.portal_types.Folder.allowed_content_types = \
            ('Document', 'Image', 'News Item', 'Topic', 'Folder', 'Folder2')

        self.portal.portal_types.Folder2.filter_content_types = 1
        self.portal.portal_types.Folder2.allowed_content_types = \
            ('Document', 'Image', 'Topic', 'Folder')

        # Set up outer folder with restrictions disabled
        self.af.setConstrainTypesMode(constraintypes.DISABLED)

        # Create type to acquire
        self.af.invokeFactory('Folder2', 'folder2', title='folder2')
        folder2 = self.af.folder2
        folder2.setConstrainTypesMode(constraintypes.ACQUIRE)

        # News item is not in addable types because it is globally forbidden in Folder2 type
        # and Folder is not in addable types because it is locally forbidden in folder2 parent
        self.assertEqual([fti.getId() for fti in folder2.allowedContentTypes()],
                             ['Document', 'Folder', 'Image', 'Topic'])
        self.assertEqual(folder2.getImmediatelyAddableTypes(),
                             ['Document', 'Folder', 'Image', 'Topic'])

        # Login the new user
        self.portal.acl_users._doAddUser('restricted', 'secret', ['Member'], [])
        folder2.manage_addLocalRoles('restricted', ('Manager',))
        user = self.portal.acl_users.getUserById('restricted')
        newSecurityManager(None, user)
        self.assertEqual([t.getId() for t in self.af.allowedContentTypes()],
                             [])
        self.assertEqual([t.getId() for t in folder2.allowedContentTypes()],
                             ['Document', 'Folder', 'Image', 'Topic'])

tests.append(TestConstrainTypes)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
