#
# Tests the one state workflow
#

from Products.CMFPlone.tests import PloneTestCase
from base import WorkflowTestCase

#from Products.CMFCore.WorkflowCore import WorkflowException

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import View
#from Products.CMFCore.permissions import ListFolderContents
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCalendar.permissions import ChangeEvents


default_user = PloneTestCase.default_user


class TestOneStateWorkflow(WorkflowTestCase):

    def afterSetUp(self):
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.workflow.setChainForPortalTypes(['Document', 'Event'], 'one_state_workflow')

        self.portal.acl_users._doAddUser('member', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret', ['Reviewer'], [])
        self.portal.acl_users._doAddUser('manager', 'secret', ['Manager'], [])
        self.portal.acl_users._doAddUser('editor', ' secret', ['Editor'], [])
        self.portal.acl_users._doAddUser('reader', 'secret', ['Reader'], [])


        self.folder.invokeFactory('Document', id='doc')
        self.doc = self.folder.doc
        self.folder.invokeFactory('Event', id='ev')
        self.ev = self.folder.ev

    # Check allowed transitions: none for one state workflow

    def testInitialState(self):
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'published')
        self.assertEqual(self.workflow.getInfoFor(self.ev, 'review_state'), 'published')

    # Check view permission

    def testViewIsNotAcquiredInPublishedState(self):
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(View), '')   # not checked

    def testViewPublishedDocument(self):
        # Owner is allowed
        self.login(default_user)
        self.failUnless(checkPerm(View, self.doc))
        # Member is allowed
        self.login('member')
        self.failUnless(checkPerm(View, self.doc))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(View, self.doc))
        # Anonymous is allowed
        self.logout()
        self.failUnless(checkPerm(View, self.doc))
        # Editor is allowed
        self.login('editor')
        self.failUnless(checkPerm(View, self.doc))
        # Reader is allowed
        self.login('reader')
        self.failUnless(checkPerm(View, self.doc))

    # Check access contents info permission

    def testAccessContentsInformationIsNotAcquiredInPublishedState(self):
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(AccessContentsInformation), '')   # not checked

    def testAccessPublishedDocument(self):
        # Owner is allowed
        self.login(default_user)
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Member is allowed
        self.login('member')
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Anonymous is allowed
        self.logout()
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Editor is allowed
        self.login('editor')
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Reader is allowed
        self.login('reader')
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))

    def testModifyPortalContentIsNotAcquiredInPublishedState(self):
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPublishedDocument(self):
        # Owner is allowed
        self.login(default_user)
        self.failUnless(checkPerm(ModifyPortalContent, self.doc))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Editor is allowed
        self.login('editor')
        self.failUnless(checkPerm(ModifyPortalContent, self.doc))
        # Reader is denied
        self.login('reader')
        self.failIf(checkPerm(ModifyPortalContent, self.doc))

    # Check change events permission

    def testChangeEventsIsNotAcquiredInPublishedState(self):
        # since r104169 event content doesn't use `ChangeEvents` anymore...
        self.assertEqual(self.ev.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPublishEvent(self):
        # Owner is allowed
        self.failUnless(checkPerm(ChangeEvents, self.ev))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Editor is allowed
        self.login('editor')
        self.failUnless(checkPerm(ChangeEvents, self.ev))
        # Reader is denied
        self.login('reader')
        self.failIf(checkPerm(ChangeEvents, self.ev))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestOneStateWorkflow))
    return suite
