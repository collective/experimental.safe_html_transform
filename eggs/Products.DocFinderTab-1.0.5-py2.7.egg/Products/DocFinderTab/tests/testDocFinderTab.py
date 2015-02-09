#
# Test DocFinderTab
#

from Testing import ZopeTestCase

ZopeTestCase.installProduct('DocFinderTab')

from AccessControl import Unauthorized
from Products.DocFinderTab.permissions import ViewDocPermission

standard_permissions = ZopeTestCase.standard_permissions
access_permissions = [ViewDocPermission]
all_permissions = standard_permissions + access_permissions


class TestDocFinderTab(ZopeTestCase.ZopeTestCase):

    def test_00_ItemPatched(self):
        '''Item should have been patched'''
        ob = getattr(self.app, 'aq_base', self.app)
        self.failUnless(hasattr(ob, 'showDocumentation'))
        self.failUnless(hasattr(ob, 'analyseDocumentation'))

    def test_01_AccessAllowed(self):
        'showDocumentation should be accessible'
        self.setPermissions(standard_permissions+access_permissions)
        try:
            dummy = self.folder.restrictedTraverse('showDocumentation')
        except Unauthorized:
            self.fail('Access to showDocumentation was denied')

    def test_02_AccessDenied(self):
        'showDocumentation should be protected'
        self.setPermissions(standard_permissions)
        try:
            dummy = self.folder.restrictedTraverse('showDocumentation')
        except Unauthorized:
            pass
        else:
            self.fail('Access to showDocumentation was allowed')

    def test_03_ManagerAccessAllowed(self):
        'showDocumentation should be accessible to Managers'
        self.setRoles(['Manager'])
        try:
            dummy = self.folder.restrictedTraverse('showDocumentation')
        except Unauthorized:
            self.fail('Access to showDocumentation was denied to Manager')

    def test_04_ManagerAccessDenied(self):
        'showDocumentation should be protected from Managers'
        self.folder.manage_permission(ViewDocPermission, ['Owner'], acquire=0)
        self.setRoles(['Manager'])
        try:
            dummy = self.folder.restrictedTraverse('showDocumentation')
        except Unauthorized:
            pass
        else:
            self.fail('Access to showDocumentation was allowed to Manager')

    def test_05_AccessAllowed(self):
        'analyseDocumentation should be accessible'
        self.setPermissions(standard_permissions+access_permissions)
        try:
            dummy = self.folder.restrictedTraverse('analyseDocumentation')
        except Unauthorized:
            self.fail('Access to analyseDocumentation was denied')

    def test_06_AccessDenied(self):
        'analyseDocumentation should be protected'
        self.setPermissions(standard_permissions)
        try:
            dummy = self.folder.restrictedTraverse('analyseDocumentation')
        except Unauthorized:
            pass
        else:
            self.fail('Access to analyseDocumentation was allowed')

    def test_07_ManagerAccessAllowed(self):
        'analyseDocumentation should be accessible to Managers'
        self.setRoles(['Manager'])
        try:
            dummy = self.folder.restrictedTraverse('analyseDocumentation')
        except Unauthorized:
            self.fail('Access to analyseDocumentation was denied to Manager')

    def test_08_ManagerAccessDenied(self):
        'analyseDocumentation should be protected from Managers'
        self.folder.manage_permission(ViewDocPermission, ['Owner'], acquire=0)
        self.setRoles(['Manager'])
        try:
            dummy = self.folder.restrictedTraverse('analyseDocumentation')
        except Unauthorized:
            pass
        else:
            self.fail('Access to analyseDocumentation was allowed to Manager')

    # b/w compatibility clutch
    if not hasattr(ZopeTestCase.ZopeTestCase, 'setPermissions'):
        setPermissions = ZopeTestCase.ZopeTestCase._setPermissions
        setRoles = ZopeTestCase.ZopeTestCase._setRoles


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestDocFinderTab))
    return suite

