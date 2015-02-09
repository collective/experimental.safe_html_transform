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
$Id: archiver.py 1824 2007-02-08 17:59:41Z hazmat $
"""

from zope.interface import implements
from zope.component import adapts

from Products.CMFCore.utils import getToolByName

import interfaces

class ContentArchiver( object ):

    implements( interfaces.IObjectArchiver )
    adapts( interfaces.IIterateAware )

    def __init__( self, context ):
        self.context = context
        self.repository = getToolByName(context, 'portal_repository')

    def save( self, checkin_message ):
        self.repository.save( self.context, checkin_message )

    def isVersionable( self ):
        if not self.repository.isVersionable( self.context ):
            return False
        return True

    def isVersioned( self ):
        archivist = getToolByName(self.context, 'portal_archivist')
        version_count = len( archivist.queryHistory( self.context ) )
        return bool( version_count )

    def isModified( self ):
        try:
            return not self.repository.isUpToDate( self.context )
        except:
            return False
