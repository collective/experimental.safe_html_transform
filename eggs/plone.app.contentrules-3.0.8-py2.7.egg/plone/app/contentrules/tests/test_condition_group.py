from zope.interface import implements
from zope.component import getUtility, getMultiAdapter

from zope.component.interfaces import IObjectEvent

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleCondition
from plone.contentrules.rule.interfaces import IExecutable

from plone.app.contentrules.conditions.group import GroupCondition
from plone.app.contentrules.conditions.group import GroupEditForm

from plone.app.contentrules.rule import Rule

from plone.app.contentrules.tests.base import ContentRulesTestCase


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, obj):
        self.object = obj


class TestGroupCondition(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testRegistered(self):
        element = getUtility(IRuleCondition, name='plone.conditions.Group')
        self.assertEqual('plone.conditions.Group', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)
        self.assertEqual(None, element.event)

    def testInvokeAddView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.Group')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+condition')
        addview = getMultiAdapter((adding, self.portal.REQUEST), name=element.addview)

        addview.createAndAdd(data={'group_names': ['Manager']})

        e = rule.conditions[0]
        self.assertTrue(isinstance(e, GroupCondition))
        self.assertEqual(['Manager'], e.group_names)

    def testInvokeEditView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.Group')
        e = GroupCondition()
        editview = getMultiAdapter((e, self.folder.REQUEST), name=element.editview)
        self.assertTrue(isinstance(editview, GroupEditForm))

    def testExecute(self):
        e = GroupCondition()
        e.group_names = ['Administrators', 'Reviewers']

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.folder)), IExecutable)
        self.assertEqual(False, ex())

        group = self.portal.portal_groups.getGroupById('Administrators')
        group.addMember(self.portal.portal_membership.getAuthenticatedMember().getId())

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.portal)), IExecutable)
        self.assertEqual(True, ex())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestGroupCondition))
    return suite
