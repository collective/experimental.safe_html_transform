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
Initialization
"""
__version__ = "$Revision: 62604 $"
# $Source: /cvsroot/ingeniweb/CMFPlacefulWorkflow/__init__.py,v $
# $Id: __init__.py 62604 2008-04-13 20:50:14Z hannosch $
__docformat__ = 'restructuredtext'

import PlacefulWorkflowTool
import DefaultWorkflowPolicy
import WorkflowPolicyConfig

from AccessControl import ModuleSecurityInfo
from Products.CMFCore import utils, DirectoryView

install_globals = globals()          # Used only in the Extensions/Install.py script

tools = (PlacefulWorkflowTool.PlacefulWorkflowTool, )

DirectoryView.registerDirectory('skins', globals())


# Initialization method
def initialize(context):
    utils.registerIcon(
        DefaultWorkflowPolicy.DefaultWorkflowPolicyDefinition,
        'images/workflow_policy.gif',
        globals())

    context.registerClass(
        PlacefulWorkflowTool.PlacefulWorkflowTool,
        meta_type="Placeful Workflow Tool",
        constructors=(PlacefulWorkflowTool.addPlacefulWorkflowTool,),
        icon = 'tool.gif')

    context.registerClass(
        WorkflowPolicyConfig.WorkflowPolicyConfig,
        permission='Add Workflow Policy',
        constructors=(WorkflowPolicyConfig.manage_addWorkflowPolicyConfigForm,
                      WorkflowPolicyConfig.manage_addWorkflowPolicyConfig),
        icon='www/WorkflowPolicyConfig_icon.gif',
    )

    utils.ToolInit( 'CMF Placeful Workflow Tool'
                  , tools=tools
                  , icon='tool.gif'
                  ).initialize( context )

ModuleSecurityInfo('Products.CMFPlacefulWorkflow').declarePublic('CMFPlacefulWorkflowMessageFactory')

# Import "CMFPlacefulWorkflowMessageFactory as _" to create messages
# Zope 3.1-style messagefactory module
# BBB: Zope 2.8 / Zope X3.0
try:
    from zope.i18nmessageid import MessageFactory
except ImportError:
    from messagefactory_ import CMFPlacefulWorkflowMessageFactory
else:
    CMFPlacefulWorkflowMessageFactory = MessageFactory('cmfplacefulworkflow')

