#
# Tests the remap-workflow functionality
#

from base import WorkflowTestCase
from plone.app.workflow.remap import remap_workflow


class TestRemapWorkflow(WorkflowTestCase):

    def afterSetUp(self):
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow

        self.setRoles(('Manager', ))

        self.workflow.setChainForPortalTypes(('Document', 'Event', ), ('simple_publication_workflow', ))
        self.workflow.setChainForPortalTypes(('News Item', ), ('one_state_workflow', ))
        self.workflow.setChainForPortalTypes(('Folder', ), ())
        self.workflow.setChainForPortalTypes(('Image', ), None)

        self.portal.invokeFactory('Document', 'd1')
        self.portal.invokeFactory('Document', 'd2')
        self.folder.invokeFactory('Event', 'e1')
        self.folder.invokeFactory('Document', 'e2')
        self.portal.invokeFactory('News Item', 'n1')
        self.portal.invokeFactory('Image', 'i1')

        self.workflow.doActionFor(self.portal.d1, 'publish')

    def _state(self, obj):
        return self.workflow.getInfoFor(obj, 'review_state')

    def _chain(self, obj):
        return self.workflow.getChainFor(obj)

    def test_remap_multiple_no_state_map(self):
        remap_workflow(self.portal,
                       type_ids=('Document', 'News Item', ),
                       chain=('plone_workflow', ))

        self.assertEquals(self._chain(self.portal.d1), ('plone_workflow', ))
        self.assertEquals(self._chain(self.portal.d2), ('plone_workflow', ))
        self.assertEquals(self._chain(self.portal.n1), ('plone_workflow', ))

        self.assertEquals(self._state(self.portal.d1), 'visible')
        self.assertEquals(self._state(self.portal.d2), 'visible')
        self.assertEquals(self._state(self.portal.n1), 'visible')

    def test_remap_with_partial_state_map(self):
        remap_workflow(self.portal,
                       type_ids=('Document', 'News Item', ),
                       chain=('plone_workflow', ),
                       state_map={'published': 'published'})

        self.assertEquals(self._chain(self.portal.d1), ('plone_workflow', ))
        self.assertEquals(self._chain(self.portal.d2), ('plone_workflow', ))
        self.assertEquals(self._chain(self.portal.n1), ('plone_workflow', ))

        self.assertEquals(self._state(self.portal.d1), 'published')
        self.assertEquals(self._state(self.portal.d2), 'visible')
        self.assertEquals(self._state(self.portal.n1), 'published')

    def test_remap_to_no_workflow(self):

        view_at_d1 = [r['name'] for r in self.portal.d1.rolesOfPermission('View') if r['selected']]
        self.failUnless('Anonymous' in view_at_d1)

        remap_workflow(self.portal,
                       type_ids=('Document', 'News Item', ),
                       chain=())

        self.assertEquals(self._chain(self.portal.d1), ())
        self.assertEquals(self._chain(self.portal.d2), ())
        self.assertEquals(self._chain(self.portal.n1), ())

        view_at_d1 = [r['name'] for r in self.portal.d1.rolesOfPermission('View') if r['selected']]
        self.failIf('Anonymous' in view_at_d1)
        self.failUnless(self.portal.d1.acquiredRolesAreUsedBy('View'))

    def test_remap_from_no_workflow(self):
        remap_workflow(self.portal,
                       type_ids=('Image', ),
                       chain=('plone_workflow', ))

        self.assertEquals(self._chain(self.portal.i1), ('plone_workflow', ))
        self.assertEquals(self._state(self.portal.i1), 'visible')

    def test_remap_to_default(self):
        remap_workflow(self.portal,
                       type_ids=('Folder', ),
                       chain='(Default)')

        self.assertEquals(self._chain(self.portal.i1), ('plone_workflow', ))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestRemapWorkflow))
    return suite
