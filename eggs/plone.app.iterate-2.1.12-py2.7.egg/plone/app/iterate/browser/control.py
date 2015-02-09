##################################################################
#
# (C) Copyright 2006 ObjectRealms, LLC
# All Rights Reserved
#
# This file is part of iterate.
#
# iterate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# iterate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iterate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################

from plone.memoize.view import memoize

from AccessControl import getSecurityManager
from Acquisition import aq_inner
from Products.Five.browser import BrowserView
from Products.Archetypes.interfaces import IReferenceable
import Products.CMFCore.permissions

from plone.app.iterate import interfaces
from plone.app.iterate.relation import WorkingCopyRelation
from plone.app.iterate import permissions

class Control(BrowserView):
    """Information about whether iterate can operate.
    
    This is a public view, referenced in action condition expressions.
    """
    
    def get_original(self, context):
        if IReferenceable.providedBy(context):
            refs = context.getRefs(WorkingCopyRelation.relationship)
            if refs:
                return refs[0]

    def checkin_allowed(self):
        """Check if a checkin is allowed
        """
        context = aq_inner(self.context)
        checkPermission = getSecurityManager().checkPermission
        
        if not interfaces.IIterateAware.providedBy(context):
            return False
    
        archiver = interfaces.IObjectArchiver(context)
        if not archiver.isVersionable():
            return False

        original = self.get_original(context)
        if original is None:
            return False

        if not checkPermission(
            Products.CMFCore.permissions.ModifyPortalContent, original):
            return False
        
        return True
        
    def checkout_allowed(self):
        """Check if a checkout is allowed.
        """
        context = aq_inner(self.context)
        
        if not interfaces.IIterateAware.providedBy(context):
            return False
        
        if not IReferenceable.providedBy(context):
            return False

        archiver = interfaces.IObjectArchiver(context)
        if not archiver.isVersionable():
            return False

        # check if there is an existing checkout
        if len(context.getBRefs(WorkingCopyRelation.relationship)) > 0:
            return False
        
        # check if its is a checkout
        if len(context.getRefs(WorkingCopyRelation.relationship)) > 0:
            return False
        
        return True
        
    @memoize
    def cancel_allowed(self):
        """Check to see if the user can cancel the checkout on the
        given working copy
        """
        return self.get_original(aq_inner(self.context)) is not None
