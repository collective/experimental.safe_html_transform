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
Product installation
"""
__version__ = "$Revision: 61118 $"
# $Source: /cvsroot/ingeniweb/CMFPlacefulWorkflow/Extensions/Install.py,v $
# $Id: Install.py 61118 2008-03-25 13:50:21Z encolpe $
__docformat__ = 'restructuredtext'

from cStringIO import StringIO

from zope.component import getSiteManager
from zope.interface import noLongerProvides

from Products.CMFPlacefulWorkflow.interfaces import IPlacefulMarker
from Products.CMFPlacefulWorkflow.global_symbols import PROJECTNAME
from Products.CMFPlacefulWorkflow.global_symbols import placeful_prefs_configlet
from Products.CMFCore.utils import getToolByName
from Products.CMFPlacefulWorkflow.interfaces import IPlacefulWorkflowTool


def uninstall(self, reinstall=False, out=None):
    if out is None:
        out = StringIO()

    getSiteManager(self).unregisterUtility(self['portal_placeful_workflow'],
                                           IPlacefulWorkflowTool)
    # uninstall configlets
    try:
        cptool = getToolByName(self, 'portal_controlpanel')
        cptool.unregisterConfiglet(placeful_prefs_configlet['id'])
        out.write('Removing CMFPlacefulWorkflow Configlet')
    except:
        out.write('Failed to remove CMFPlacefulWorkflow Configlet')

    wf_tool = getToolByName(self, 'portal_workflow')
    if IPlacefulMarker.providedBy(wf_tool):
        noLongerProvides(wf_tool, IPlacefulMarker)

    return out.getvalue()
