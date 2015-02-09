##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Upgrade tests. """

import unittest
from Testing import ZopeTestCase

import transaction
from os.path import abspath
from os.path import dirname
from os.path import join as path_join

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
from Products.CMFCore.tests.base.testcase import WarningInterceptor
from Products.CMFDefault.testing import FunctionalLayer
from Products.GenericSetup.context import TarballImportContext
from zope.site.hooks import setSite

here = abspath(dirname(__file__))


class FunctionalUpgradeTestCase(ZopeTestCase.FunctionalTestCase,
                                WarningInterceptor):

    layer = FunctionalLayer
    _setup_fixture = 0

    def afterSetUp(self):
        zexp_path = path_join(here, '%s.zexp' % self._SITE_ID)
        self._trap_warning_output()
        self.app._importObjectFromFile(zexp_path, verify=0)
        self._free_warning_output()
        transaction.commit()

    def beforeTearDown(self):
        self.app._delObject(self._SITE_ID)
        transaction.commit()

    def testUpgradeAllProposed(self):
        request = self.app.REQUEST
        oldsite = getattr(self.app, self._SITE_ID)
        stool = oldsite.portal_setup
        profile_id = 'Products.CMFDefault:default'
        upgrades = []
        for upgrade_info in stool.listUpgrades(profile_id):
            if isinstance(upgrade_info, list):
                for info in upgrade_info:
                    if info['proposed']:
                        upgrades.append(info['id'])
                continue
            if upgrade_info['proposed']:
                upgrades.append(upgrade_info['id'])

        request.form['profile_id'] = profile_id
        request.form['upgrades'] = upgrades
        stool.manage_doUpgrades(request)

        self.assertEqual(stool.getLastVersionForProfile(profile_id),
                         ('2', '2'))

        newSecurityManager(None, UnrestrictedUser('god', '', ['Manager'], ''))
        setSite(self.app.site)
        expected_export = self.app.site.portal_setup.runAllExportSteps()
        setSite(oldsite)
        upgraded_export = stool.runAllExportSteps()

        expected = TarballImportContext(stool, expected_export['tarball'])
        upgraded = TarballImportContext(stool, upgraded_export['tarball'])
        diff = stool.compareConfigurations(upgraded, expected)
        self.assertEqual(diff, '', diff)


class UpgradeFrom20Tests(FunctionalUpgradeTestCase):

    _SITE_ID = 'cmf20Site'


class UpgradeFrom21Tests(FunctionalUpgradeTestCase):

    _SITE_ID = 'cmf21Site'


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UpgradeFrom20Tests),
        unittest.makeSuite(UpgradeFrom21Tests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
