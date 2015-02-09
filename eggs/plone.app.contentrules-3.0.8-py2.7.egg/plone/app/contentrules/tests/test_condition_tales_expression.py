from zope.interface import implements
from zope.component import getUtility, getMultiAdapter

from zope.component.interfaces import IObjectEvent

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleCondition
from plone.contentrules.rule.interfaces import IExecutable

from plone.app.contentrules.conditions.talesexpression import TalesExpressionCondition
from plone.app.contentrules.conditions.talesexpression import TalesExpressionEditForm

from plone.app.contentrules.rule import Rule

from plone.app.contentrules.tests.base import ContentRulesTestCase


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, obj):
        self.object = obj


class TestTalesExpressionCondition(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testRegistered(self):
        element = getUtility(IRuleCondition, name='plone.conditions.TalesExpression')
        self.assertEqual('plone.conditions.TalesExpression', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)

    def testInvokeAddView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.TalesExpression')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+condition')
        addview = getMultiAdapter((adding, self.portal.REQUEST), name=element.addview)

        addview.createAndAdd(data={'tales_expression': 'python:"plone" in object.Subject()'})

        e = rule.conditions[0]
        self.assertTrue(isinstance(e, TalesExpressionCondition))
        self.assertEqual('python:"plone" in object.Subject()', e.tales_expression)

    def testInvokeEditView(self):
        element = getUtility(IRuleCondition, name='plone.conditions.TalesExpression')
        e = TalesExpressionCondition()
        editview = getMultiAdapter((e, self.folder.REQUEST), name=element.editview)
        self.assertTrue(isinstance(editview, TalesExpressionEditForm))

    def testExecute(self):
        e = TalesExpressionCondition()
        e.tales_expression = 'python:"plone" in object.Subject()'

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.folder)), IExecutable)
        self.assertEqual(False, ex())

        ex = getMultiAdapter((self.portal, e, DummyEvent(self.portal)), IExecutable)
        self.assertEqual(False, ex())

        self.folder.setSubject(('plone', 'contentrules'))
        ex = getMultiAdapter((self.portal, e, DummyEvent(self.folder)), IExecutable)
        self.assertEqual(True, ex())

    def testExecuteUnicodeString(self):
        e = TalesExpressionCondition()
        e.tales_expression = u'string:${portal_url}'
        ex = getMultiAdapter((self.portal, e, DummyEvent(self.folder)), IExecutable)
        self.assertEqual(True, ex())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTalesExpressionCondition))
    return suite
