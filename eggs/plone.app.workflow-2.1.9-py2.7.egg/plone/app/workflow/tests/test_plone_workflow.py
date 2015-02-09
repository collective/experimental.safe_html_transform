#
# Tests the default workflow
#

from Products.CMFPlone.tests import PloneTestCase
from base import WorkflowTestCase

from Products.CMFCore.WorkflowCore import WorkflowException

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCalendar.permissions import ChangeEvents

default_user = PloneTestCase.default_user


class TestDefaultWorkflow(WorkflowTestCase):

    def afterSetUp(self):
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow

        self.workflow.setChainForPortalTypes(['Document', 'Event'], 'plone_workflow')

        self.portal.acl_users._doAddUser('member', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret', ['Reviewer'], [])
        self.portal.acl_users._doAddUser('manager', 'secret', ['Manager'], [])

        self.folder.invokeFactory('Document', id='doc')
        self.doc = self.folder.doc

        self.folder.invokeFactory('Event', id='ev')
        self.ev = self.folder.ev

    # Check allowed transitions

    def testOwnerHidesVisibleDocument(self):
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'private')
        self.failUnless(self.catalog(id='doc', review_state='private'))

    def testOwnerShowsPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'private')
        self.workflow.doActionFor(self.doc, 'show')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='doc', review_state='visible'))

    def testOwnerSubmitsVisibleDocument(self):
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'pending')
        self.failUnless(self.catalog(id='doc', review_state='pending'))

    def testOwnerRetractsPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'pending')
        self.workflow.doActionFor(self.doc, 'retract')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='doc', review_state='visible'))

    def testOwnerRetractsPublishedDocument(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'published')
        self.login(default_user)
        self.workflow.doActionFor(self.doc, 'retract')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='doc', review_state='visible'))

    def testReviewerPublishesPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'pending')
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'published')
        self.failUnless(self.catalog(id='doc', review_state='published'))

    def testReviewerRejectsPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'pending')
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'reject')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='doc', review_state='visible'))

    def testReviewerPublishesVisibleDocument(self):
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'published')
        self.failUnless(self.catalog(id='doc', review_state='published'))

    def testReviewerRejectsPublishedDocument(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'published')
        self.workflow.doActionFor(self.doc, 'reject')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.failUnless(self.catalog(id='doc', review_state='visible'))

    # Check some forbidden transitions

    def testOwnerPublishesVisibleDocument(self):
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'visible')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.doc, 'publish')

    def testOwnerSubmitsPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'private')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.doc, 'submit')

    def testManagerPublishesPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.workflow.getInfoFor(self.doc, 'review_state'), 'private')
        self.login('manager')
        self.assertRaises(WorkflowException, self.workflow.doActionFor, self.doc, 'publish')

    # No way am I going to write tests for all impossible transitions ;-)

    # Check view permission

    def testViewVisibleDocument(self):
        # Owner is allowed
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

    def testViewIsNotAcquiredInVisibleState(self):
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(View), '')

    def testViewPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        # Owner is allowed
        self.failUnless(checkPerm(View, self.doc))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(View, self.doc))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(View, self.doc))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(View, self.doc))

    def testViewIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(View), '')

    def testViewPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        # Owner is allowed
        self.failUnless(checkPerm(View, self.doc))
        # Member is allowed (TODO:?)
        self.login('member')
        self.failUnless(checkPerm(View, self.doc))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(View, self.doc))
        # Anonymous is allowed (TODO:?)
        self.logout()
        self.failUnless(checkPerm(View, self.doc))

    def testViewIsNotAcquiredInPendingState(self):
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(View), '')

    def testViewPublishedDocument(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
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

    def testViewIsNotAcquiredInPublishedState(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(View), '')

    # Check access contents info permission

    def testAccessVisibleDocument(self):
        # Owner is allowed
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

    def testAccessContentsInformationIsNotAcquiredInVisibleState(self):
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    def testAccessPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        # Owner is allowed
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(AccessContentsInformation, self.doc))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(AccessContentsInformation, self.doc))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(AccessContentsInformation, self.doc))

    def testAccessContentsInformationIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    def testAccessPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        # Owner is allowed
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Member is allowed (TODO:?)
        self.login('member')
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))
        # Anonymous is allowed (TODO:?)
        self.logout()
        self.failUnless(checkPerm(AccessContentsInformation, self.doc))

    def testAccessContentsInformationIsNotAcquiredInPendingState(self):
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    def testAccessPublishedDocument(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
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

    def testAccessContentsInformationIsNotAcquiredInPublishedState(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(AccessContentsInformation), '')

    # Check modify content permissions

    def testModifyVisibleDocument(self):
        # Owner is allowed
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

    def testModifyPortalContentIsNotAcquiredInVisibleState(self):
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        # Owner is allowed
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

    def testModifyPortalContentIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.doc, 'hide')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        # Owner is denied
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(ModifyPortalContent, self.doc))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ModifyPortalContent, self.doc))

    def testModifyPortalContentIsNotAcquiredInPendingState(self):
        self.workflow.doActionFor(self.doc, 'submit')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPublishedDocument(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        # Owner is denied
        self.login(default_user)
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ModifyPortalContent, self.doc))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ModifyPortalContent, self.doc))

    def testModifyPortalContentIsNotAcquiredInPublishedState(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        self.assertEqual(self.doc.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    # Check change events permission

    def testModifyVisibleEvent(self):
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

    def testChangeEventsIsNotAcquiredInVisibleState(self):
        # since r104169 event content doesn't use `ChangeEvents` anymore...
        self.assertEqual(self.ev.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPrivateEvent(self):
        self.workflow.doActionFor(self.ev, 'hide')
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

    def testChangeEventsIsNotAcquiredInPrivateState(self):
        self.workflow.doActionFor(self.ev, 'hide')
        # since r104169 event content doesn't use `ChangeEvents` anymore...
        self.assertEqual(self.ev.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPendingEvent(self):
        self.workflow.doActionFor(self.ev, 'submit')
        # Owner is denied
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(checkPerm(ChangeEvents, self.ev))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ChangeEvents, self.ev))

    def testChangeEventsIsNotAcquiredInPendingState(self):
        self.workflow.doActionFor(self.ev, 'submit')
        # since r104169 event content doesn't use `ChangeEvents` anymore...
        self.assertEqual(self.ev.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    def testModifyPublishedEvent(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.ev, 'publish')
        # Owner is denied
        self.login(default_user)
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Member is denied
        self.login('member')
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(checkPerm(ChangeEvents, self.ev))
        # Anonymous is denied
        self.logout()
        self.failIf(checkPerm(ChangeEvents, self.ev))

    def testChangeEventsIsNotAcquiredInPublishedState(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.ev, 'publish')
        # since r104169 event content doesn't use `ChangeEvents` anymore...
        self.assertEqual(self.ev.acquiredRolesAreUsedBy(ModifyPortalContent), '')

    # Check catalog search

    def testFindVisibleDocument(self):
        # Owner is allowed
        self.failUnless(self.catalog(id='doc'))
        # Member is allowed
        self.login('member')
        self.failUnless(self.catalog(id='doc'))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(self.catalog(id='doc'))
        # Anonymous is allowed
        self.logout()
        self.failUnless(self.catalog(id='doc'))

    def testFindPrivateDocument(self):
        self.workflow.doActionFor(self.doc, 'hide')
        # Owner is allowed
        self.failUnless(self.catalog(id='doc'))
        # Member is denied
        self.login('member')
        self.failIf(self.catalog(id='doc'))
        # Reviewer is denied
        self.login('reviewer')
        self.failIf(self.catalog(id='doc'))
        # Anonymous is denied
        self.logout()
        self.failIf(self.catalog(id='doc'))

    def testFindPendingDocument(self):
        self.workflow.doActionFor(self.doc, 'submit')
        # Owner is allowed
        self.failUnless(self.catalog(id='doc'))
        # Member is allowed (TODO:?)
        self.login('member')
        self.failUnless(self.catalog(id='doc'))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(self.catalog(id='doc'))
        # Anonymous is allowed (TODO:?)
        self.logout()
        self.failUnless(self.catalog(id='doc'))

    def testFindPublishedDocument(self):
        self.login('reviewer')
        self.workflow.doActionFor(self.doc, 'publish')
        # Owner is allowed
        self.login(default_user)
        self.failUnless(self.catalog(id='doc'))
        # Member is allowed
        self.login('member')
        self.failUnless(self.catalog(id='doc'))
        # Reviewer is allowed
        self.login('reviewer')
        self.failUnless(self.catalog(id='doc'))
        # Anonymous is allowed
        self.logout()
        self.failUnless(self.catalog(id='doc'))

    def testMyWorklist(self):
        # When a member has the local Reviewer role, pending
        # docs should show up in his worklist.
        self.workflow.doActionFor(self.doc, 'submit')
        self.doc.manage_addLocalRoles('member', ['Reviewer'])
        self.login('reviewer')
        worklist = self.portal.my_worklist()
        self.failUnless(len(worklist) == 1)
        self.failUnless(worklist[0] == self.doc)
        self.login('member')
        worklist = self.portal.my_worklist()
        self.failUnless(len(worklist) == 1)
        self.failUnless(worklist[0] == self.doc)

    def testStateTitles(self):
        state_titles = {'private': 'Private',
                        'visible': 'Public draft',
                        'pending': 'Pending review',
                        'published': 'Published'}

        wf = self.workflow.plone_workflow

        for state_id, title in state_titles.items():
            state = getattr(wf.states, state_id, None)
            if state is not None:
                self.assertEqual(state.title, title)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestDefaultWorkflow))
    return suite
