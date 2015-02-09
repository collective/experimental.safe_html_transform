from zope.component import getUtility, getMultiAdapter

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleCondition
from plone.contentrules.rule.interfaces import IExecutable

from plone.app.contentrules.conditions.wftransition import WorkflowTransitionCondition
from plone.app.contentrules.conditions.wftransition import WorkflowTransitionEditForm

from plone.app.contentrules.rule import Rule

from plone.app.contentrules.tests.base import ContentRulesTestCase

from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFCore.WorkflowCore import ActionSucceededEvent


class TestWorkflowTransitionCondition(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testRegistered(self):
        element = getUtility(IRuleCondition, name='plone.conditions.WorkflowTransition')
        self.assertEqual('plone.conditions.WorkflowTransition', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)
        self.assertEqual(IActionSucceededEvent, element.event)

    def testInvokeAddView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.WorkflowTransition')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+condition')
        addview = getMultiAdapter((adding, self.portal.REQUEST), name=element.addview)

        addview.createAndAdd(data={'wf_transitions': ['publish', 'hide']})

        e = rule.conditions[0]
        self.assertTrue(isinstance(e, WorkflowTransitionCondition))
        self.assertEqual(['publish', 'hide'], e.wf_transitions)

    def testInvokeEditView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.WorkflowTransition')
        e = WorkflowTransitionCondition()
        editview = getMultiAdapter((e, self.folder.REQUEST), name=element.editview)
        self.assertTrue(isinstance(editview, WorkflowTransitionEditForm))

    def testExecute(self):
        e = WorkflowTransitionCondition()
        e.wf_transitions = ['publish', 'hide']

        ex = getMultiAdapter((self.portal, e,
                              ActionSucceededEvent(self.folder, 'dummy_workflow', 'publish', None)),
                             IExecutable)
        self.assertEqual(True, ex())

        ex = getMultiAdapter((self.portal, e,
                              ActionSucceededEvent(self.folder, 'dummy_workflow', 'retract', None)),
                             IExecutable)
        self.assertEqual(False, ex())

        ex = getMultiAdapter((self.portal, e,
                              ActionSucceededEvent(self.folder, 'dummy_workflow', 'hide', None)),
                             IExecutable)
        self.assertEqual(True, ex())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestWorkflowTransitionCondition))
    return suite
