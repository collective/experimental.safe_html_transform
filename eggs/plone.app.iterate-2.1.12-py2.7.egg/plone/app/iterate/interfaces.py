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
$Id: interfaces.py 1811 2007-02-06 18:40:02Z hazmat $
"""

from zope.interface import Interface, Attribute
from zope import schema

from zope.component.interfaces import IObjectEvent
from plone.locking.interfaces import LockType

from Products.Archetypes.interfaces import IReference

#################################
## Marker interface

class IIterateAware( Interface ):
    """An object that can be used for check-in/check-out operations.
    """

#################################
## Lock types

ITERATE_LOCK = LockType( u'iterate.lock', stealable=False, user_unlockable=False )

#################################
## Exceptions

class CociException( Exception ):
    pass

class CheckinException( CociException ):
    pass

class CheckoutException( CociException ):
    pass

class ConflictError( CheckinException ):
    pass


#################################
# Annotation Key
annotation_key = "ore.iterate"

class keys( object ):
    # various common keys
    checkout_user = "checkout_user"
    checkout_time = "checkout_time"



#################################
## Event Interfaces

class ICheckinEvent( IObjectEvent ):
    """ a working copy is being checked in, event.object is the working copy, this
    message is sent before any mutation/merge has been done on the objects
    """

    baseline = Attribute("The Working Copy's baseline")
    relation = Attribute("The Working Copy Archetypes Relation Object")
    checkin_message = Attribute("checkin message")
    
class IAfterCheckinEvent( IObjectEvent ):
    """ sent out after an object is checked in """

    checkin_message = Attribute("checkin message")

class IBeforeCheckoutEvent( IObjectEvent ):
    """ sent out before a working copy is created """
    
class ICheckoutEvent( IObjectEvent ):
    """ an object is being checked out, event.object is the baseline """

    working_copy = Attribute("The object's working copy")
    relation = Attribute("The Working Copy Archetypes Relation Object")
    
class ICancelCheckoutEvent( IObjectEvent ):
    """ a working copy is being cancelled """
    
    baseline = Attribute("The working copy's baseline")

class IWorkingCopyDeletedEvent( IObjectEvent ):
    """ a working copy is being deleted, this gets called multiple times at different
    states. so on cancel checkout and checkin operations, its mostly designed to
    broadcast an event when the user deletes a working copy using the standard
    container paradigms.
    """
    
    baseline = Attribute("The working copy baseline")
    relation = Attribute("The Working Copy Archetypes Relation Object")    
    
#################################
# Content Marker Interfaces

class IIterateManagedContent ( Interface ):
    """Any content managed by iterate - normally a sub-interface is
    applied as a marker to an instance.
    """

class IWorkingCopy( IIterateManagedContent ):
    """A working copy/check-out
    """

class IBaseline( IIterateManagedContent ):
    """A baseline
    """

class IWorkingCopyRelation( IReference ):
    """A relationship to a working copy
    """

#################################
## Working copy container locator

class IWCContainerLocator( Interface ):
    """A named adapter capable of discovering containers where working
    copies can be created.
    """
    
    available = schema.Bool(title=u"Available", description=u"Whether location will be available.")

    title = schema.TextLine(title=u"Title", description=u"Title of this location")
    
    def __call__():
        """Return a container object, or None if available() is False
        """

#################################
## Interfaces

class ICheckinCheckoutTool( Interface ):

    def allowCheckin( content ):
        """
        denotes whether a checkin operation can be performed on the content.
        """
        
    def allowCheckout( content ):
        """
        denotes whether a checkout operation can be performed on the content.        
        """

    def allowCancelCheckout( content ):
        """
        denotes whether a cancel checkout operation can be performed on the content.        
        """        

    def checkin( content, checkin_messsage ):
        """
        check the working copy in, this will merge the working copy with the baseline
       
        """

    def checkout( container, content ):
        """
        """

    def cancelCheckout( content ):
        """
        """


class IObjectCopier( Interface ):
    """ copies and merges the object state
    """

    def copyTo( container ):
        """ copy the context to the given container, must also create an AT relation
        using the WorkingCopyRelation.relation name between the source and the copy.
        returns the copy.
        """
        
    def merge( ):
        """ merge/replace the source with the copy, context is the copy.
        """

class IObjectArchiver( Interface ):
    """ iterate needs minimal versioning support
    """

    def save( checkin_message ):
        """ save a new version of the object
        """

    def isVersioned( self ):
        """ is this content already versioned
        """
        
    def isVersionable( self ):
        """ is versionable check.
        """

    def isModified( self ):
        """ is the resource current state, different than its last saved state.
        """

class ICheckinCheckoutPolicy( Interface ):
    """
    Checkin / Checkout Policy
    """

    def checkin( checkin_message ):
        """
        checkin the context, if the target has been deleted then raises a checkin exception.
        
#       if the object version has changed since the checkout begin (due to another checkin)
#       raises a conflict error.
#        
        """

    def checkout( container ):
        """
        checkout the content object into the container, iff another object with
        the same id exists the id is amended, the working copy object is returned.

        the content object is locked during checkout.

        raises a CheckoutError if the object is already checked out.
        """

    def cancelCheckout( ):
        """
        coxtent is a checkout (working copy), this method will go ahead and delete
        the working copy.
        """

    def getWorkingCopies( ):
        """
        """

##     def merge( content ):
##         """
##         if there are known conflicts between the checkout and the checkedin version,
##         using the merge method signals that conflicts have been resolved in the working
##         copy.
##         """


#################################

class ICheckinCheckoutReference( Interface ):
    # a reference processor

    def checkout( baseline, wc, references, storage ):
        """
        handle processing of the given references from the baseline
        into the working copy, storage is an annotation for bookkeeping
        information.
        """

    def checkoutBackReferences( baseline, wc, references, storage ):
        """
        """

    def checkin( baseline, wc, references, storage ):
        """
        """

    def checkinBackReferences( baseline, wc, references, storage ):
        """
        """
