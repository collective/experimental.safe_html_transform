# -*- coding: utf-8 -*-

import time

from plone.contentrules.engine.interfaces import IRuleAssignmentManager
from plone.contentrules.engine.interfaces import IRuleStorage
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.context import TarballExportContext
from Products.PloneTestCase.layer import PloneSite

from plone.app.contentrules.tests.base import ContentRulesTestCase
from plone.app.contentrules.tests.test_configuration import TestContentrulesGSLayer
from plone.app.contentrules.api import edit_rule_assignment

# BBB Zope 2.12
try:
    from Zope2.App import zcml
    from OFS import metaconfigure
except ImportError:
    from Products.Five import zcml
    from Products.Five import fiveconfigure as metaconfigure


class TestCascadingRule(ContentRulesTestCase):

    layer = TestContentrulesGSLayer

    def afterSetUp(self):
        self.storage = getUtility(IRuleStorage)
        self.loginAsPortalOwner()
        if 'news' not in self.portal:
            self.portal.invokeFactory('Folder', 'news')

        self.portal.news.setLocallyAllowedTypes(['News Item', 'Event'])
        if 'events' not in self.portal:
            self.portal.invokeFactory('Folder', 'events')

        portal_setup = self.portal.portal_setup
        portal_setup.runAllImportStepsFromProfile('profile-plone.app.contentrules:testing')
        edit_rule_assignment(self.portal, 'test4', bubbles=1, enabled=1)
        edit_rule_assignment(self.portal, 'test5', bubbles=1, enabled=1)

    def test_cascading_rule(self):
        # check that test2 rule and test4 rule are executed
        # test2 rule publishes the event in news folder
        # test4 rule moves it in events folder when it is published
        self.portal.news.invokeFactory('Event', 'my-event')
        event = self.portal.news['my-event']
        event.processForm()
        self.assertFalse('my-event' in self.portal.news)
        self.assertTrue('my-event' in self.portal.events)

        wtool = self.portal.portal_workflow
        self.assertTrue(wtool.getInfoFor(self.portal.events['my-event'], 'review_state'),
                        'published')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCascadingRule))
    return suite
