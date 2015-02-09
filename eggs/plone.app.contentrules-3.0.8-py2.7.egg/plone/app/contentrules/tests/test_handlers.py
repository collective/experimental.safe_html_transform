from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent

from plone.app.contentrules.tests import base
from plone.app.contentrules.tests import dummy
from plone.app.contentrules import handlers


class TestDuplicateRuleFilter(base.ContentRulesTestCase):

    def setUp(self):
        super(TestDuplicateRuleFilter, self).setUp()
        self.setRoles(('Manager', ))
        self.context = self.folder
        self.event = dummy.DummyEvent(self.context)
        self.rulefilter = handlers.DuplicateRuleFilter()
        self.rule = dummy.DummyRule()
        self.uuidaware = dummy.DummyNonArchetypesContext()
        notify(ObjectCreatedEvent(self.uuidaware))

    def test_call_archetypescontext(self):
        to_execute = self.rulefilter(self.context, self.rule, self.event)
        self.assertTrue(to_execute)
        to_execute = self.rulefilter(self.context, self.rule, self.event)
        self.assertTrue(not to_execute)

    def test_call_two_events_in_same_context(self):
        # if events on two different objects are handled in the same context,
        # they are not filtered
        to_execute = self.rulefilter(self.context, self.rule, self.event)
        self.assertTrue(to_execute)
        self.portal.invokeFactory('Folder', 'folder2')
        event2 = dummy.DummyEvent(self.portal.folder2)
        to_execute = self.rulefilter(self.context, self.rule, event2)
        self.assertTrue(to_execute)

    def test_call_uuidaware(self):
        to_execute = self.rulefilter(self.uuidaware, self.rule, self.event)
        self.assertTrue(to_execute)
        to_execute = self.rulefilter(self.uuidaware, self.rule, self.event)
        self.assertTrue(not to_execute)

    def test_delayed_events(self):
        # many events can be delayed
        self.loginAsPortalOwner()
        self.portal.invokeFactory('Folder', 'folder2')

        event1 = dummy.DummyEvent(self.folder)
        event2 = dummy.DummyEvent(self.portal.folder2)

        from plone.app.contentrules.handlers import _status
        _status.delayed_events = {}
        handlers.added(event1)
        handlers.added(event2)
        from plone.app.contentrules.handlers import _status
        self.assertEqual(len(_status.delayed_events), 2)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestDuplicateRuleFilter))
    return suite
