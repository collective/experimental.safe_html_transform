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

from zope.annotation import IAnnotations
from persistent.dict import PersistentDict
from interfaces import annotation_key
from Products.CMFCore.utils import getToolByName

def get_storage( context ):
    annotations = IAnnotations( context )
    if not annotations.has_key( annotation_key ):
        annotations[ annotation_key ] = PersistentDict()
    return annotations[annotation_key]

def upgrade_by_reinstall(context):
    qi = getToolByName(context, 'portal_quickinstaller')
    qi.reinstallProducts(['plone.app.iterate'])
