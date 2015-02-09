# -*- coding: utf-8 -*-
# $Id: tests.py 246098 2011-11-02 10:10:59Z glenfant $
"""Testing"""

from Testing import ZopeTestCase
import Products.Five
from Products.Five import zcml as five_zcml
from Products.Five import fiveconfigure
import aws.zope2zcmldoc
from aws.zope2zcmldoc.config import CONTROLPANEL_ID, ZOPE_VERSION

if ZOPE_VERSION > (2, 13):
    from Zope2.App import zcml as five_zcml
else:
    from Products.Five import zcml as five_zcml

fiveconfigure.debug_mode = True
five_zcml.load_config('meta.zcml', Products.Five)
five_zcml.load_config('configure.zcml', Products.Five)
five_zcml.load_config('configure.zcml', aws.zope2zcmldoc)
fiveconfigure.debug_mode = False

ZopeTestCase.installPackage('aws.zope2zcmldoc')

_marker = {}


class TestZCMLDoc(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        # Installing the Control panel
        self.setRoles(['Manager'], name='test_user_1_')
        self.app.unrestrictedTraverse('@@install-aws-zope2zcmldoc')()
        return

    def beforeTearDown(self):
        # Removing control panel
        self.app.unrestrictedTraverse('@@uninstall-aws-zope2zcmldoc')()
        return

    def _getControlPanel(self):
        cp = self.app.Control_Panel
        return cp[CONTROLPANEL_ID]

    def _getControlPanelView(self, name, form=_marker):
        cp = self._getControlPanel()
        view = cp.unrestrictedTraverse(name)
        if form != _marker:
            view.request.form = form
        return view

    def test_have_controlpanel(self):
        """Control panel installation
        """
        cp = self.app.Control_Panel
        self.failUnless(CONTROLPANEL_ID in cp.objectIds(), "Control panel is not installed")
        return

    def test_cp_namespaces(self):
        # We have some base namespaces available from old times
        cp = self._getControlPanel()
        expected = ('', 'http://namespaces.zope.org/zope', 'http://namespaces.zope.org/meta')
        expected = set(expected)
        namespaces = set(cp.getNamespaces())
        self.failUnless(namespaces >= expected, "Some base namespaces are missing")
        return

    def test_cp_subdirs(self):
        # We have subdirectives for some directives
        cp = self._getControlPanel()
        expected = (('http://namespaces.zope.org/browser', u'menuItems'),
                    ('http://namespaces.zope.org/zope', u'class'))
        expected = set(expected)
        subdirs = set(cp.getSubdirs())
        self.failUnless(subdirs >= expected, "Some base namespaces are missing")
        return

    def test_manage_main(self):
        view = self._getControlPanelView('@@manage_main')
        for ns in view.namespaces():
            self.failUnless('view_url' in ns, "Missing view URL")
            self.failUnless('namespace_url' in ns, "Missing namespace URL")
        return

    def test_view_namespace(self):
        query = {'ns': 'http://namespaces.zope.org/zope'}
        view = self._getControlPanelView('@@view_namespace', form=query)
        directives = view.list_directives()
        for directive in directives:
            self.failUnless('name' in directive, "Directive has no name")
            self.failUnless('view_url' in directive, "Directive has no view URL")
        return

    def test_view_directive(self):
        query = {
            'ns': 'http://namespaces.zope.org/zope',
            'directive': 'class'
            }
        view = self._getControlPanelView('@@view_directive', form=query)
        subdirs = view.list_subdirectives()
        self.failUnless(len(subdirs) > 0, "'class' should have subdirectives")
        infos = view.directive_infos()
        self.failUnlessEqual(len(infos.attributes()), 1, "Only one attribute is required for 'class'")
        if ZOPE_VERSION > (2, 13):
            expected = 'AccessControl.metaconfigure.ClassDirective'
        else:
            expected = 'Products.Five.metaconfigure.ClassDirective'
        self.failUnlessEqual(infos.python_handler(), expected)
        return


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestZCMLDoc))
    return suite
