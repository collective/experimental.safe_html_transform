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
# along with CMFDeployment; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################
"""
$Id: relation.py 1392 2006-06-20 01:02:17Z hazmat $
"""

from zope.interface import implements
from zope.component import adapts
from zope.annotation.interfaces import IAttributeAnnotatable

from Products.Archetypes import config as atconf
from Products.Archetypes.ReferenceEngine import Reference

from interfaces import IWorkingCopyRelation
from interfaces import ICheckinCheckoutReference
from interfaces import IIterateAware


class WorkingCopyRelation( Reference ):
    """
    Source Object is Working Copy

    Target Object is Baseline Version
    """
    relationship = "Working Copy Relation"

    implements( IWorkingCopyRelation, IAttributeAnnotatable )


class CheckinCheckoutReferenceAdapter ( object ):
    """
    default adapter for references.

    on checkout
    
    forward refs on baseline are copied to wc
    backward refs on baseline are ignored on wc

    on checkin

    forward refs on wc are kept
    backwards refs on wc are kept

    forward refs on baseline get removed
    backward refs on baseline are kept by virtue of UID transferance
    
    """

    implements( ICheckinCheckoutReference )
    adapts( IIterateAware )
    
    storage_key = "coci.references"

    def __init__(self, context ):
        self.context = context
    
    def checkout( self, baseline, wc, refs, storage ):
        for ref in refs:
            wc.addReference( ref.targetUID, ref.relationship, referenceClass=ref.__class__ )
            
    def checkin( self, *args ):
        pass

    checkoutBackReferences = checkinBackReferences = checkin



class NoCopyReferenceAdapter( object ):
    """
    an adapter for references that does not copy them to the wc on checkout.

    additionally custom reference state is kept when the wc is checked in.
    """

    implements( ICheckinCheckoutReference )

    def __init__(self, context):
        self.context = context
    
    def checkin( self, baseline, wc, refs, storage ):
        # move the references from the baseline to the wc

        # one note, on checkin the wc uid is not yet changed to match that of the baseline
        ref_ids = [r.getId() for r in refs]

        baseline_ref_container = getattr( baseline, atconf.REFERENCE_ANNOTATION )
        clipboard = baseline_ref_container.manage_cutObjects( ref_ids )

        wc_ref_container = getattr( wc, atconf.REFERENCE_ANNOTATION )

        # references aren't globally addable w/ associated perm which default copysupport
        # wants to check, temporarily monkey around the issue.
        def _verifyObjectPaste( *args, **kw ): pass
        wc_ref_container._verifyObjectPaste = _verifyObjectPaste
        try:
            wc_ref_container.manage_pasteObjects( clipboard )
        finally:
            del wc_ref_container._verifyObjectPaste

    def checkout( self, *args ):
        pass
        
    checkoutBackReferences = checkinBackReferences = checkout
    
