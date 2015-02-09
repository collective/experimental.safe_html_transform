import unittest2 as unittest

from Acquisition import aq_base

from zope.component import getUtility
from plone.registry.interfaces import IRegistry

from plone.app.registry.testing import PLONE_APP_REGISTRY_INTEGRATION_TESTING


class TestSetup(unittest.TestCase):

    layer = PLONE_APP_REGISTRY_INTEGRATION_TESTING

    def test_tool_installed(self):

        portal = self.layer['portal']

        self.failUnless('portal_registry' in portal.objectIds())
        self.failUnless(IRegistry.providedBy(portal.portal_registry))

    def test_local_utility_installed(self):
        portal = self.layer['portal']

        registry = getUtility(IRegistry)
        self.failUnless(aq_base(registry) is aq_base(portal.portal_registry))
