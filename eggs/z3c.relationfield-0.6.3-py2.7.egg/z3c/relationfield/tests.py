from unittest import makeSuite, TestCase, TestSuite
from z3c.relationfield.testing import (
    register_fake_intid,
    register_fake_catalog,
    unregister_fake_intid,
    unregister_fake_catalog,
    MockContent,
)
from z3c.relationfield import event
from z3c.relationfield import RelationList, Relation
from zope.component.interfaces import ObjectEvent
from zope.component.interfaces import ComponentLookupError


class FieldTests(TestCase):
    """Unit tests for fields
    """

    def test_list_value_type(self):
        f = RelationList(title=u"Test")
        self.failUnless(isinstance(f.value_type, Relation))


class EventTests(TestCase):
    """Unit tests for the relation field event handlers.  The event handlers
    should be tolerant of missing utilities and objects not yet registered with
    the intid utility."""

    def setUp(self):
        self.content = MockContent()
        register_fake_catalog()
        register_fake_intid()

    def tearDown(self):
        unregister_fake_catalog()
        unregister_fake_intid()

    def test_missing_intids(self):
        """Event handlers which trigger on object removal should not
        throw exceptions when the utilities are missing.  The utilities may
        have been deleted in the same transaction (e.g. site deletion)."""
        # Remove intid utility and ensure the event handler doesn't fail
        unregister_fake_intid()
        try:
            event.breakRelations(ObjectEvent(self.content))
        except ComponentLookupError:
            self.fail("breakRelations fails when intid utility is missing")

    def test_break_relations_missing_catalog(self):
        # Remove relations catalog and ensure the event handler doesn't fail
        unregister_fake_catalog()
        try:
            event.breakRelations(ObjectEvent(self.content))
        except ComponentLookupError:
            self.fail("breakRelations fails when catalog utility is missing")

    def test_remove_relations_missing_catalog(self):
        # Remove relations catalog and ensure the event handler doesn't fail
        unregister_fake_catalog()
        try:
            event.removeRelations(self.content, None)
        except ComponentLookupError:
            self.fail("removeRelations fails when catalog utility is missing")

    def test_initid_failure(self):
        """When an object has not yet been registered with the intid utility,
        getId fails with a KeyError.  The event handlers need to handle this
        cleanly."""
        # Our content is not yet registered with the intid utility
        # and has no __parent__ attribute
        try:
            event.updateRelations(self.content, None)
        except (KeyError, AttributeError):
            self.fail("updateRelations fails with unregistered object")


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(EventTests))
    suite.addTest(makeSuite(FieldTests))
    return suite
