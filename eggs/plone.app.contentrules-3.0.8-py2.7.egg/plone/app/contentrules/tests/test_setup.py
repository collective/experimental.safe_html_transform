from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from plone.contentrules.engine.interfaces import IRuleAssignable
from plone.contentrules.rule.interfaces import IRuleEventType

from plone.app.contentrules.tests.base import ContentRulesTestCase


class TestProductInstall(ContentRulesTestCase):

    def testRuleContainerInterfaces(self):
        self.assertTrue(IRuleAssignable.providedBy(self.folder))
        self.assertTrue(IRuleAssignable.providedBy(self.portal))

    def testEventTypesMarked(self):
        self.assertTrue(IRuleEventType.providedBy(IObjectAddedEvent))
        self.assertTrue(IRuleEventType.providedBy(IObjectModifiedEvent))
        self.assertTrue(IRuleEventType.providedBy(IObjectRemovedEvent))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestProductInstall))
    return suite
