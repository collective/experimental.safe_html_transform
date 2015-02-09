## -*- coding: utf-8 -*-
## Copyright (C) 2008 Ingeniweb

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

__version__ = "$Revision: $"
# $Source: $
# $Id: $
__docformat__ = 'restructuredtext'

from zope.interface import alsoProvides
from Products.CMFCore.utils import getToolByName
from Products.CMFPlacefulWorkflow.interfaces import IPlacefulMarker

def installMarker(context):
    """
    Apply a marker interface to the workflow tool to indicate that the
    product is installed.
    """
    # Only run step if a flag file is present (e.g. not an extension profile)
    if context.readDataFile('placeful_marker.txt') is None:
        return
    site = context.getSite()
    wf = getToolByName(site, 'portal_workflow', None)
    if wf is not None:
        alsoProvides(wf, IPlacefulMarker)
