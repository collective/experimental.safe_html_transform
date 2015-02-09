from zope.component import getUtility

from Acquisition import aq_base, aq_parent

from plone.contentrules.engine.interfaces import IRuleStorage

from plone.app.contentrules.rule import Rule
from plone.app.contentrules.tests.base import ContentRulesTestCase

from dummy import DummyCondition, DummyAction


class TestTraversal(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testTraverseToRule(self):
        r = Rule()
        storage = getUtility(IRuleStorage)
        storage[u'r1'] = r
        traversed = self.portal.restrictedTraverse('++rule++r1')
        self.assertTrue(aq_parent(traversed) is self.portal)
        self.assertTrue(aq_base(traversed) is r)

    def testTraverseToRuleCondition(self):
        r = Rule()
        e1 = DummyCondition()
        e1.x = "x"

        e2 = DummyCondition()
        e2.x = "y"

        r.conditions.append(e1)
        r.conditions.append(e2)
        storage = getUtility(IRuleStorage)
        storage[u'r1'] = r

        tr = self.portal.restrictedTraverse('++rule++r1')
        te1 = tr.restrictedTraverse('++condition++0')
        te2 = tr.restrictedTraverse('++condition++1')

        self.assertTrue(aq_parent(te1) is tr)
        self.assertEqual("x", te1.x)

        self.assertTrue(aq_parent(te2) is tr)
        self.assertEqual("y", te2.x)

    def testTraverseToRuleAction(self):
        r = Rule()
        e1 = DummyAction()
        e1.x = "x"

        e2 = DummyAction()
        e2.x = "y"

        r.actions.append(e1)
        r.actions.append(e2)
        storage = getUtility(IRuleStorage)
        storage[u'r1'] = r

        tr = self.portal.restrictedTraverse('++rule++r1')
        te1 = tr.restrictedTraverse('++action++0')
        te2 = tr.restrictedTraverse('++action++1')

        self.assertTrue(aq_parent(te1) is tr)
        self.assertEqual("x", te1.x)

        self.assertTrue(aq_parent(te2) is tr)
        self.assertEqual("y", te2.x)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTraversal))
    return suite
