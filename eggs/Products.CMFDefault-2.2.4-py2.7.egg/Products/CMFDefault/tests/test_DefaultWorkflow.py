##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for DefaultWorkflow module. """

import unittest
import Testing

from zope.interface.verify import verifyClass

from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFCore.tests.base.dummy import DummySite
from Products.CMFCore.tests.base.dummy import DummyTool
from Products.CMFCore.tests.base.dummy import DummyUserFolder
from Products.CMFCore.WorkflowTool import WorkflowTool


class DefaultWorkflowDefinitionTests(unittest.TestCase):

    def setUp(self):
        from Products.CMFDefault.DefaultWorkflow \
                import DefaultWorkflowDefinition
        self.site = DummySite('site')
        self.site._setObject('portal_types', DummyTool())
        self.site._setObject('portal_workflow', WorkflowTool())
        self.site._setObject('portal_membership', DummyTool())
        self.site._setObject('acl_users', DummyUserFolder())

        wftool = self.site.portal_workflow
        wftool._setObject('wf', DefaultWorkflowDefinition('wf'))
        wftool.setDefaultChain('wf')

    def test_interfaces(self):
        from Products.CMFCore.interfaces import IWorkflowDefinition
        from Products.CMFDefault.DefaultWorkflow \
                import DefaultWorkflowDefinition

        verifyClass(IWorkflowDefinition, DefaultWorkflowDefinition)

    def _getDummyWorkflow(self):
        wftool = self.site.portal_workflow
        return wftool.wf

    def test_isActionSupported(self):

        wf = self._getDummyWorkflow()
        dummy = self.site._setObject('dummy', DummyContent())

        for action in ('submit', 'retract', 'publish', 'reject',):
            self.assert_(wf.isActionSupported(dummy, action))

    def test_isActionSupported_with_keywargs(self):

        wf = self._getDummyWorkflow()
        dummy = self.site._setObject('dummy', DummyContent())

        for action in ('submit', 'retract', 'publish', 'reject',):
            self.assert_(wf.isActionSupported(dummy, action,
                                              arg1=1, arg2=2))

    # XXX more tests...


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DefaultWorkflowDefinitionTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
