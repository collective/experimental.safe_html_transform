from plone.app.contentrules.tests.base import ContentRulesTestCase


class TestEvents(ContentRulesTestCase):

    def testEventHandlerExecutesRules(self):
        # XXX Test missing
        pass

    def testEventHandlerExecutesRulesOnlyOnce(self):
        # XXX Test missing
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestEvents))
    return suite
