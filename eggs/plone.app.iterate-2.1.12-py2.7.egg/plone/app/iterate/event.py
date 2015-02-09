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
$Id: event.py 1811 2007-02-06 18:40:02Z hazmat $
"""
from zope.interface import implements
from zope.event import notify
from zope.component.interfaces import ObjectEvent

import interfaces
import relation

class CheckoutEvent( ObjectEvent ):

    implements( interfaces.ICheckoutEvent )

    def __init__(self, baseline, wc, relation):
        ObjectEvent.__init__(self, baseline )
        self.working_copy = wc
        self.relation = relation
        
class CheckinEvent( ObjectEvent ):

    implements( interfaces.ICheckinEvent )

    def __init__(self, wc, baseline, relation, message):
        ObjectEvent.__init__( self, wc )
        self.baseline = baseline
        self.relation = relation
        self.message = message

class AfterCheckinEvent( ObjectEvent ):

    implements( interfaces.IAfterCheckinEvent )
    
    def __init__( self, new_baseline, checkin_message ):
        super( AfterCheckinEvent, self).__init__( new_baseline )
        self.message = checkin_message

class CancelCheckoutEvent( ObjectEvent ):

    implements( interfaces.ICancelCheckoutEvent )

    def __init__( self, wc, baseline):
        ObjectEvent.__init__(self, wc )
        self.baseline = baseline

class WorkingCopyDeletedEvent( ObjectEvent ):

    implements( interfaces.IWorkingCopyDeletedEvent )

    def __init__( self, wc, baseline, relation ):
        ObjectEvent.__init__( self, wc )
        self.baseline = baseline
        self.relation = relation

class BeforeCheckoutEvent( ObjectEvent ):

    implements( interfaces.IBeforeCheckoutEvent )
    

def handleDeletion( reference, event ):
    # a filtering/enriching event rebroadcaster for working copy deletions
    workingCopy = reference.getSourceObject()
    baseline = reference.getTargetObject()
    notify( WorkingCopyDeletedEvent( workingCopy, baseline, reference ) )
    
