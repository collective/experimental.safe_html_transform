import doctest
import unittest

import zope.component
from Products.GenericSetup import EXTENSION, profile_registry
from plone.app import testing
from plone.testing import layered

from Products.CMFQuickInstallerTool.QuickInstallerTool import QuickInstallerTool
from Products.CMFQuickInstallerTool.events import handleBeforeProfileImportEvent
from Products.CMFQuickInstallerTool.events import handleProfileImportedEvent

OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

TEST_PATCHES = {}


class QuickInstallerCaseFixture(testing.PloneSandboxLayer):

    defaultBases = (testing.PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        sm = zope.component.getSiteManager()
        sm.registerHandler(handleBeforeProfileImportEvent)
        sm.registerHandler(handleProfileImportedEvent)

        profile_registry.registerProfile(
            'test',
            'CMFQI test profile',
            'Test profile for CMFQuickInstallerTool',
            'profiles/test',
            'Products.CMFQuickInstallerTool',
            EXTENSION,
            for_=None)

    def setUpPloneSite(self, portal):
        TEST_PATCHES['orig_isProductInstallable'] = QuickInstallerTool.isProductInstallable

        def patched_isProductInstallable(self, productname):
            if 'QITest' in productname or 'CMFQuickInstallerTool' in productname:
                return True
            return TEST_PATCHES['orig_isProductInstallable'](self, productname)
        QuickInstallerTool.isProductInstallable = patched_isProductInstallable

    def tearDownPloneSite(self, portal):
        QuickInstallerTool.isProductInstallable = TEST_PATCHES['orig_isProductInstallable']

        profile_registry.unregisterProfile('test', 'Products.CMFQuickInstallerTool')

        sm = zope.component.getSiteManager()
        sm.unregisterHandler(handleBeforeProfileImportEvent)
        sm.unregisterHandler(handleProfileImportedEvent)

CQI_FIXTURE = QuickInstallerCaseFixture()
CQI_FUNCTIONAL_TESTING = testing.FunctionalTesting(
    bases=(CQI_FIXTURE, ), name='CMFQuickInstallerToolTest:Functional')


def test_suite():
    suite = unittest.TestSuite()
    for testfile in ['actions.txt', 'profiles.txt', 'install.txt']:
        suite.addTest(layered(
            doctest.DocFileSuite(
                'actions.txt',
                package='Products.CMFQuickInstallerTool.tests',
                optionflags=OPTIONFLAGS),
            layer=CQI_FUNCTIONAL_TESTING))
    return suite
