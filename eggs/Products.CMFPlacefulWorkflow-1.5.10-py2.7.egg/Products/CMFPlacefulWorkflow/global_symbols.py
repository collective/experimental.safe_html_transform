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
CMFPlacefulWorkflow product
"""
__version__ = "$Revision: 43896 $"
# $Source: /cvsroot/ingeniweb/CMFPlacefulWorkflow/global_symbols.py,v $
# $Id: global_symbols.py 43896 2007-06-17 09:55:34Z hannosch $
__docformat__ = 'restructuredtext'

import os

# Check if we have to be in debug mode
if os.path.isfile(os.path.abspath(os.path.dirname(__file__)) + '/debug.txt'):
    DEBUG_MODE = True
else:
    DEBUG_MODE = False

# Set log options correctly
import Log
if DEBUG_MODE:
    Log.LOG_LEVEL = Log.LOG_DEBUG
else:
    Log.LOG_LEVEL = Log.LOG_NOTICE

from Log import *

PROJECTNAME = "CMFPlacefulWorkflow"

from Products.CMFPlacefulWorkflow.permissions import ManageWorkflowPolicies

placeful_prefs_configlet = {
    'id': 'placefulworkflow',
    'appId': "Placeful Workflow",
    'name': 'Placeful Workflow',
    'action': 'string:$portal_url/prefs_workflow_localpolicies_form',
    'category': 'Products',
    'permission': (ManageWorkflowPolicies,),
    'imageUrl': 'placefulworkflow_icon.png',
    }
