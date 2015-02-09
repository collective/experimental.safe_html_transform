##################################################################
#
# (C) Copyright 2006-2007 ObjectRealms, LLC
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
A Default Checkin Checkout Policy For Content

$Id: policy.py 1824 2007-02-08 17:59:41Z hazmat $
"""

from zope import component
from zope.event import notify
from zope.interface import implements
from zope.annotation.interfaces import IAnnotations

from Acquisition import Implicit, aq_base, aq_inner, aq_parent

import interfaces
import event
import lock

from relation import WorkingCopyRelation

class CheckinCheckoutPolicyAdapter( object ):
    """
    Default Checkin Checkout Policy For Content
    
    on checkout context is the baseline
    
    on checkin context is the working copy
    """
    
    implements( interfaces.ICheckinCheckoutPolicy )
    component.adapts( interfaces.IIterateAware )

    # used when creating baseline version for first time
    default_base_message = "Created Baseline"
    
    def __init__( self, context ):
        self.context = context

    def checkout( self, container ):
        # see interface
        notify( event.BeforeCheckoutEvent( self.context ) )

        # use the object copier to checkout the content to the container
        copier = component.queryAdapter( self.context, interfaces.IObjectCopier )
        working_copy, relation = copier.copyTo( container )

        # publish the event for any subscribers
        notify( event.CheckoutEvent( self.context, working_copy, relation ) )
       
        # finally return the working copy 
        return working_copy

    def checkin( self, checkin_message ):
        # see interface

        # get the baseline for this working copy, raise if not found
        baseline = self._getBaseline()

        # get a hold of the relation object
        wc_ref = self.context.getReferenceImpl( WorkingCopyRelation.relationship )[ 0]
        
        # publish the event for subscribers, early because contexts are about to be manipulated
        notify( event.CheckinEvent( self.context, baseline, wc_ref, checkin_message ) )

        # merge the object back to the baseline with a copier
        
        # XXX by gotcha
        # bug we should or use a getAdapter call or test if copier is None
        copier = component.queryAdapter( self.context, interfaces.IObjectCopier )
        new_baseline = copier.merge()

        # don't need to unlock the lock disappears with old baseline deletion
        notify( event.AfterCheckinEvent( new_baseline, checkin_message ) )
        
        return new_baseline

    def cancelCheckout( self ):
        # see interface
        
        # get the baseline
        baseline = self._getBaseline()

        # publish an event
        notify( event.CancelCheckoutEvent( self.context, baseline ) )
        
        # delete the working copy        
        wc_container =  aq_parent( aq_inner( self.context ) )
        wc_container.manage_delObjects( [ self.context.getId() ] )

        return baseline

    #################################
    ## Checkin Support Methods

    def _getBaseline( self ):
        # follow the working copy's reference back to the baseline
        refs = self.context.getRefs( WorkingCopyRelation.relationship )

        if not len(refs) == 1:
            raise interfaces.CheckinException( "Baseline count mismatch" )

        if not refs or refs[0] is None:
            raise interfaces.CheckinException( "Baseline has disappeared" )

        baseline = refs[0]
        return baseline