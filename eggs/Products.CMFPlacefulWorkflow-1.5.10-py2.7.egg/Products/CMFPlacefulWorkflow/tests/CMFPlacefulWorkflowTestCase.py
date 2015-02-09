# -*- coding: utf-8 -*-
## CMFPlacefulWorkflow
## Copyright (C)2005 Ingeniweb

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING. If not, write to the
## Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
CMFPlacefulWorkflow TestCase module
"""
__version__ = "$Revision: 41292 $"
# $Source: /cvsroot/ingeniweb/CMFPlacefulWorkflow/tests/CMFPlacefulWorkflowTestCase.py,v $
# $Id: CMFPlacefulWorkflowTestCase.py 41292 2007-04-29 21:20:27Z optilude $
__docformat__ = 'restructuredtext'

# Zope imports
from Testing import ZopeTestCase
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

# Plone imports
from Products.PloneTestCase import PloneTestCase


class CMFPlacefulWorkflowTestCase(PloneTestCase.PloneTestCase):

    # Globals
    portal_name = 'portal'
    portal_owner = 'portal_owner'
    user_name = PloneTestCase.default_user
    user_password = PloneTestCase.default_password

    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def _setup(self):
        PloneTestCase.PloneTestCase._setup(self)
        self.app.REQUEST['SESSION'] = self.Session()

    def beforeTearDown(self):
        # logout
        noSecurityManager()

    def loginAsPortalMember(self):
        '''Use if you need to manipulate site as a member.'''
        self._setupUser()
        self.mtool.createMemberarea(self.user_name)
        member = self.mtool.getMemberById(self.user_name)
        member.setMemberProperties({'fullname': self.user_name.capitalize(),
                                    'email': 'test@example.com', })
        self.login()

    def loginAsPortalOwner(self):
        '''Use if you need to manipulate site as a manager.'''
        uf = self.app.acl_users
        user = uf.getUserById(self.portal_owner).__of__(uf)
        newSecurityManager(None, user)

    def getPermissionsOfRole(self, role):
        perms = self.portal.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]


class CMFPlacefulWorkflowFunctionalTestCase(
    CMFPlacefulWorkflowTestCase, PloneTestCase.FunctionalTestCase):
    pass

# Install CMFPlacefulWorkflow
ZopeTestCase.installProduct('CMFPlacefulWorkflow')

# Setup Plone site
PloneTestCase.setupPloneSite(id='plone', products=[
    'CMFPlacefulWorkflow',
    ], extension_profiles=[
    'Products.CMFPlone:testfixture',
    ])

app = ZopeTestCase.app()
ZopeTestCase.close(app)
