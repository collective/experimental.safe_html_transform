#
# Tests the folder workflow
#

from base import WorkflowTestCase

from Products.CMFCore.WorkflowCore import WorkflowException

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ListFolderContents
from Products.CMFCore.permissions import ModifyPortalContent


class TestFolderWorkflow(WorkflowTestCase):

    def afterSetUp(self):
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow

        self.workflow.setChainForPortalTypes(['Folder'], 'folder_workflow')

        self.portal.acl_users._doAddUser('member', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret', ['Reviewer'], [])
        self.portal.acl_users._doAddUser('manager', 'secret', ['Manager'], [])

        self.folder.invokeFactory('Folder', id='dir')
        self.dir = self.folder.dir

    # Check allowed transitions

    def testOwnerHidesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.failUnless(self.catalog(id='dir', review_state='private'))

    def testOwnerShowsPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.workflow.doActionFor(self.dir, 'show')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='dir', review_state='visible'))

    def testOwnerPublishesPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.failUnless(self.catalog(id='dir', review_state='published'))

    def testOwnerPublishesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.failUnless(self.catalog(id='dir', review_state='published'))

    def testOwnerHidesPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.failUnless(self.catalog(id='dir', review_state='private'))

    def testOwnerRetractsPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.workflow.doActionFor(self.dir, 'retract')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='dir', review_state='visible'))

    def testManagerPublishesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.login('manager')
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.failUnless(self.catalog(id='dir', review_state='published'))

    def testManagerPublishesPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.login('manager')
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.failUnless(self.catalog(id='dir', review_state='published'))

    def testManagerRetractsPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.login('manager')
        self.workflow.doActionFor(self.dir, 'retract')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='dir', review_state='visible'))

    # Check forbidden transitions

    def testMemberHidesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.login('member')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'hide')

    def testMemberShowsPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.login('member')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'show')

    def testMemberPublishesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.login('member')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'publish')

    def testMemberPublishesPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.login('member')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'publish')

    def testMemberHidesPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.login('member')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'hide')

    def testMemberRetractsPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.login('member')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'retract')

    def testReviewerHidesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.login('reviewer')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'hide')

    def testReviewerShowsPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.login('reviewer')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'show')

    def testReviewerPublishesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.login('reviewer')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'publish')

    def testReviewerPublishesPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.login('reviewer')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'publish')

    def testReviewerHidesPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.login('reviewer')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'hide')

    def testReviewerRetractsPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.login('reviewer')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.dir, 'retract')

    def testManagerHidesVisibleFolder(self):
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'visible')
        self.login('manager')
        self.workflow.doActionFor(self.dir, 'hide')

    def testManagerShowsPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'private')
        self.login('manager')
        self.workflow.doActionFor(self.dir, 'show')

    def testManagerHidesPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.dir, 'review_state'), 'published')
        self.login('manager')
        self.workflow.doActionFor(self.dir, 'hide')

    # Check view permissions

    def testViewVisibleFolder(self):
        # Owner is allowed
        self.failUnless(checkPerm(View, self.dir))
        # Member is allowed
        self.login('member')
        self.failUnless(checkPerm(View, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(View, self.dir))
        # Anonymous is allowed
        self.logout()
        self.failUnless(checkPerm(View, self.dir))

    def testViewIsNotAcquiredInVisibleState(self):
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(View), '')

    def testViewPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        # Owner is allowed
        self.failUnless(checkPerm(View, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(View, self.dir))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(View, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(View, self.dir))

    def testViewIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(View), '')

    def testViewPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        # Owner is allowed
        self.failUnless(checkPerm(View, self.dir))
        # Member is allowed
        self.login('member')
        self.failUnless(checkPerm(View, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(View, self.dir))
        # Anonymous is allowed
        self.logout()
        self.failUnless(checkPerm(View, self.dir))

    def testViewIsNotAcquiredInPublishedState(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(View), '')

    # Check access contents info permission

    def testAccessVisibleFolderContents(self):
        # Owner is allowed
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Member is allowed
        self.login('member')
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Anonymous is allowed
        self.logout()
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))

    def testAccessContentsInformationIsNotAcquiredInVisibleState(self):
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    def testAccessPrivateFolderContents(self):
        self.workflow.doActionFor(self.dir, 'hide')
        # Owner is allowed
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(AccessContentsInformation, self.dir))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(AccessContentsInformation, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(AccessContentsInformation, self.dir))

    def testAccessContentsInformationIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    def testAccessPublishedFolderContents(self):
        self.workflow.doActionFor(self.dir, 'publish')
        # Owner is allowed
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Member is allowed
        self.login('member')
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))
        # Anonymous is allowed
        self.logout()
        self.failUnless(checkPerm(AccessContentsInformation, self.dir))

    def testAccessContentsInformationIsNotAcquiredInPublishedState(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    # Check modify contents permission

    def testModifyVisibleFolderContents(self):
        # Owner is allowed
        self.failUnless(checkPerm(ModifyPortalContent, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ModifyPortalContent, self.dir))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ModifyPortalContent, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ModifyPortalContent, self.dir))

    def testModifyPortalContentIsNotAcquiredInVisibleState(self):
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPrivateFolderContents(self):
        self.workflow.doActionFor(self.dir, 'hide')
        # Owner is allowed
        self.failUnless(checkPerm(ModifyPortalContent, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ModifyPortalContent, self.dir))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ModifyPortalContent, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ModifyPortalContent, self.dir))

    def testModifyPortalContentIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPublishedFolderContents(self):
        self.workflow.doActionFor(self.dir, 'publish')
        # Owner is allowed
        self.failUnless(checkPerm(ModifyPortalContent, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ModifyPortalContent, self.dir))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ModifyPortalContent, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ModifyPortalContent, self.dir))

    def testModifyPortalContentIsNotAcquiredInPublishedState(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    # Check list contents permission

    def testListVisibleFolderContents(self):
        # Owner is allowed
        self.failUnless(checkPerm(ListFolderContents, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ListFolderContents, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(ListFolderContents, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ListFolderContents, self.dir))

    def testListFolderContentsIsAcquiredInVisibleState(self):
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(ListFolderContents), 'CHECKED')

    def testListPrivateFolderContents(self):
        self.workflow.doActionFor(self.dir, 'hide')
        # Owner is allowed
        self.failUnless(checkPerm(ListFolderContents, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ListFolderContents, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(ListFolderContents, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ListFolderContents, self.dir))

    def testListFolderContentsIsAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.dir, 'hide')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(ListFolderContents), 'CHECKED')

    def testListPublishedFolderContents(self):
        self.workflow.doActionFor(self.dir, 'publish')
        # Owner is allowed
        self.failUnless(checkPerm(ListFolderContents, self.dir))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ListFolderContents, self.dir))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(ListFolderContents, self.dir))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ListFolderContents, self.dir))

    def testListFolderContentsNotAcquiredInPublishedState(self):
        self.workflow.doActionFor(self.dir, 'publish')
        self.assertEqual(self.dir.acquiredRolesAreUsedBy(ListFolderContents), 'CHECKED')

    # Check catalog search

    def testFindVisibleFolder(self):
        # Owner is allowed
        self.failUnless(self.catalog(id='dir'))
        # Member is allowed
        self.login('member')
        self.failUnless(self.catalog(id='dir'))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(self.catalog(id='dir'))
        # Anonymous is allowed
        self.logout()
        self.failUnless(self.catalog(id='dir'))

    def testFindPrivateFolder(self):
        self.workflow.doActionFor(self.dir, 'hide')
        # Owner is allowed
        self.failUnless(self.catalog(id='dir'))
        # Member is denied
        self.login('member')
        self.failIf(self.catalog(id='dir'))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(self.catalog(id='dir'))
        # Anonymous is denied
        self.logout()
        self.failIf(self.catalog(id='dir'))

    def testFindPublishedFolder(self):
        self.workflow.doActionFor(self.dir, 'publish')
        # Owner is allowed
        self.failUnless(self.catalog(id='dir'))
        # Member is allowed
        self.login('member')
        self.failUnless(self.catalog(id='dir'))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(self.catalog(id='dir'))
        # Anonymous is allowed
        self.logout()
        self.failUnless(self.catalog(id='dir'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFolderWorkflow))
    return suite
