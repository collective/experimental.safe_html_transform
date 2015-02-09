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
""" Unit tests for MembershipTool module. """

import unittest
import Testing

from AccessControl.SecurityManagement import newSecurityManager
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from Products.CMFCore.PortalFolder import PortalFolder
from Products.CMFCore.tests.base.dummy import DummyFolder
from Products.CMFCore.tests.base.dummy import DummySite
from Products.CMFCore.tests.base.dummy import DummyTool
from Products.CMFCore.tests.base.dummy import DummyUserFolder
from Products.CMFCore.tests.base.testcase import SecurityTest


class MembershipToolTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFDefault.MembershipTool import MembershipTool

        return MembershipTool(*args, **kw)

    def setUp(self):
        self.site = DummySite('site')
        self.site._setObject( 'portal_membership', self._makeOne() )

    def test_interfaces(self):
        from Products.CMFDefault.interfaces import IMembershipTool
        from Products.CMFDefault.MembershipTool import MembershipTool

        verifyClass(IMembershipTool, MembershipTool)

    def test_MembersFolder_methods(self):
        mtool = self.site.portal_membership
        self.assertEqual( mtool.getMembersFolder(), None )
        self.site._setObject( 'Members', DummyFolder() )
        self.assertEqual( mtool.getMembersFolder(), self.site.Members )
        mtool.setMembersFolderById(id='foo')
        self.assertEqual( mtool.getMembersFolder(), None )
        self.site._setObject( 'foo', DummyFolder() )
        self.assertEqual( mtool.getMembersFolder(), self.site.foo )
        mtool.setMembersFolderById( id='foo/members' )
        self.assertEqual( mtool.getMembersFolder(), None )
        self.site.foo._setObject( 'members', DummyFolder() )
        self.assertEqual( mtool.getMembersFolder(), self.site.foo.members )
        mtool.setMembersFolderById()
        # Note: self.site is returned due to DummyObject.restrictedTraverse
        self.assertEqual( mtool.getMembersFolder(), self.site )


class MembershipToolSecurityTests(SecurityTest):

    def _makeOne(self, *args, **kw):
        from Products.CMFDefault.MembershipTool import MembershipTool

        return MembershipTool(*args, **kw)

    def setUp(self):
        SecurityTest.setUp(self)
        self.site = DummySite('site').__of__(self.root)
        self.site._setObject( 'portal_membership', self._makeOne() )

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)

    def test_createMemberArea(self):
        mtool = self.site.portal_membership
        members = self.site._setObject( 'Members', PortalFolder('Members') )
        acl_users = self.site._setObject( 'acl_users', DummyUserFolder() )
        wtool = self.site._setObject( 'portal_workflow', DummyTool() )

        # permission
        mtool.createMemberArea('user_foo')
        self.failIf( hasattr(members.aq_self, 'user_foo') )
        newSecurityManager(None, acl_users.user_bar)
        mtool.createMemberArea('user_foo')
        self.failIf( hasattr(members.aq_self, 'user_foo') )
        newSecurityManager(None, acl_users.user_foo)
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea('user_foo')
        self.failIf( hasattr(members.aq_self, 'user_foo') )
        newSecurityManager(None, acl_users.all_powerful_Oz)
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea('user_foo')
        self.failUnless( hasattr(members.aq_self, 'user_foo') )

        # default content
        f = members.user_foo
        ownership = acl_users.user_foo
        localroles = ( ( 'user_foo', ('Owner',) ), )
        self.assertEqual( f.Title(), "user_foo's Home" )
        self.assertEqual( f.getOwner(), ownership )
        self.assertEqual( f.get_local_roles(), localroles,
                          'CMF Collector issue #162 (LocalRoles broken): %s'
                          % str( f.get_local_roles() ) )
        self.assertEqual( f.index_html.getOwner(), ownership,
                          'CMF Collector issue #162 (Ownership broken): %s'
                          % str( f.index_html.getOwner() ) )
        self.assertEqual( f.index_html.get_local_roles(), localroles,
                          'CMF Collector issue #162 (LocalRoles broken): %s'
                          % str( f.index_html.get_local_roles() ) )
        self.assertEqual( wtool.test_notified, f.index_html )

        # acquisition
        self.site.user_bar = 'test attribute'
        newSecurityManager(None, acl_users.user_bar)
        mtool.createMemberArea('user_bar')
        self.failUnless( hasattr(members.aq_self, 'user_bar'),
                         'CMF Collector issue #102 (acquisition bug)' )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MembershipToolTests),
        unittest.makeSuite(MembershipToolSecurityTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
