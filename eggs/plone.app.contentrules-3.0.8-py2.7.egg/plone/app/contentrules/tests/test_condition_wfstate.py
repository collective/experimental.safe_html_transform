from zope.interface import implements
from zope.component import getUtility, getMultiAdapter

from zope.component.interfaces import IObjectEvent

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleCondition
from plone.contentrules.rule.interfaces import IExecutable

from plone.app.contentrules.conditions.wfstate import WorkflowStateCondition
from plone.app.contentrules.conditions.wfstate import WorkflowStateEditForm

from plone.app.contentrules.rule import Rule

from plone.app.contentrules.tests.base import ContentRulesTestCase


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, obj):
        self.object = obj


class TestWorkflowStateCondition(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testRegistered(self):
        element = getUtility(IRuleCondition, name='plone.conditions.WorkflowState')
        self.assertEqual('plone.conditions.WorkflowState', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)
        self.assertEqual(IObjectEvent, element.event)

    def testInvokeAddView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.WorkflowState')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+condition')
        addview = getMultiAdapter((adding, self.portal.REQUEST), name=element.addview)

        addview.createAndAdd(data={'wf_states': ['visible', 'published']})

        e = rule.conditions[0]
        self.assertTrue(isinstance(e, WorkflowStateCondition))
        self.assertEqual(['visible', 'published'], e.wf_states)

    def testInvokeEditView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.WorkflowState')
        e = WorkflowStateCondition()
        editview = getMultiAdapter((e, self.folder.REQUEST), name=element.editview)
        self.assertTrue(isinstance(editview, WorkflowStateEditForm))

    def testExecute(self):
        e = WorkflowStateCondition()
        e.wf_states = ['visible', 'private']

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.folder)), IExecutable)
        self.assertEqual(True, ex())

        self.portal.portal_workflow.doActionFor(self.folder, 'publish')

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.folder)), IExecutable)
        self.assertEqual(False, ex())

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.portal)), IExecutable)
        self.assertEqual(False, ex())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestWorkflowStateCondition))
    return suite
