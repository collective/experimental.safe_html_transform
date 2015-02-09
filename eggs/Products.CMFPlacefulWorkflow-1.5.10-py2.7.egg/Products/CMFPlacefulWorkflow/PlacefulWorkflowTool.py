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
PlacefulWorkflowTool main class
"""
__version__ = "$Revision: 62441 $"
# $Source: /cvsroot/ingeniweb/CMFPlacefulWorkflow/PlacefulWorkflowTool.py,v $
# $Id: PlacefulWorkflowTool.py 62441 2008-04-10 20:03:21Z encolpe $
__docformat__ = 'restructuredtext'

from os.path import join as path_join

from AccessControl.requestmethod import postonly
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from Acquisition import aq_parent
from App.class_init import InitializeClass
from OFS.Folder import Folder
from OFS.ObjectManager import IFAwareObjectManager

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import ImmutableId
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import _checkPermission

from Products.CMFCore.interfaces import ISiteRoot

from Products.CMFPlacefulWorkflow.permissions import ManageWorkflowPolicies
from interfaces import IPlacefulWorkflowTool

WorkflowPolicyConfig_id = ".wf_policy_config"
_MARKER = object()

def safeEditProperty(obj, key, value, data_type='string'):
    """ An add or edit function, surprisingly useful :) """
    if obj.hasProperty(key):
        obj._updateProperty(key, value)
    else:
        obj._setProperty(key, value, data_type)

def addPlacefulWorkflowTool(self,REQUEST={}):
    """
    Factory method for the Placeful Workflow Tool
    """
    id='portal_placeful_workflow'
    pwt=PlacefulWorkflowTool()
    self._setObject(id, pwt, set_owner=0)
    getattr(self, id)._post_init()
    if REQUEST:
        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')

class PlacefulWorkflowTool(ImmutableId, Folder, IFAwareObjectManager):
    """
    PlacefulWorkflow Tool
    """

    id = 'portal_placeful_workflow'
    meta_type = 'Placeful Workflow Tool'

    implements(IPlacefulWorkflowTool)

    _actions = []

    security = ClassSecurityInfo()


    manage_options=Folder.manage_options

    def __init__(self):
        # Properties to be edited by site manager
        safeEditProperty(self, 'max_chain_length', 1, data_type='int')

    _manage_addWorkflowPolicyForm = PageTemplateFile(path_join('www', 'add_workflow_policy'), globals())

    security.declareProtected(ManageWorkflowPolicies, 'manage_addWorkflowPolicyForm')
    def manage_addWorkflowPolicyForm(self, REQUEST):
        """ Form for adding workflow policies.
        """
        wfpt = []
        for key in _workflow_policy_factories.keys():
            wfpt.append(key)
        wfpt.sort()
        return self._manage_addWorkflowPolicyForm(REQUEST, workflow_policy_types=wfpt)

    security.declareProtected(ManageWorkflowPolicies, 'manage_addWorkflowPolicy')
    def manage_addWorkflowPolicy(self, id,
                                 workflow_policy_type='default_workflow_policy (Simple Policy)',
                                 duplicate_id='empty',
                                 RESPONSE=None,
                                 REQUEST=None):
        """ Adds a workflow policies from the registered types.
        """
        if id in ('empty', 'portal_workflow'):
            raise ValueError, "'%s' is reserved. Please choose another id." % id

        factory = _workflow_policy_factories[workflow_policy_type]
        ob = factory(id)
        self._setObject(id, ob)

        if duplicate_id and duplicate_id != 'empty':
            types_tool = getToolByName(self, 'portal_types')
            new_wp = self.getWorkflowPolicyById(id)

            if duplicate_id == 'portal_workflow':
                wf_tool = getToolByName(self, 'portal_workflow')

                new_wp.setDefaultChain(wf_tool._default_chain)

                for ptype in types_tool.objectIds():
                    chain = wf_tool.getChainForPortalType(ptype, managescreen=True)
                    if chain:
                        new_wp.setChain(ptype, chain)

            else:
                orig_wp = self.getWorkflowPolicyById(duplicate_id)
                new_wp.setDefaultChain(orig_wp.getDefaultChain('Document'))

                for ptype in types_tool.objectIds():
                    chain = orig_wp.getChainFor(ptype, managescreen=True)
                    if chain:
                        new_wp.setChain(ptype, chain)

        if RESPONSE is not None:
            RESPONSE.redirect(self.absolute_url() +
                              '/manage_main?management_view=Contents')
    manage_addWorkflowPolicy = postonly(manage_addWorkflowPolicy)

    def all_meta_types(self):
        return (
            {'name': 'WorkflowPolicy',
             'action': 'manage_addWorkflowPolicyForm',
             'permission':ManageWorkflowPolicies },)

    security.declareProtected(ManageWorkflowPolicies, 'getWorkflowPolicyById')
    def getWorkflowPolicyById(self, wfp_id):
        """ Retrieve a given workflow policy.
        """
        if wfp_id is None:
            return None
        policy = getattr(self.aq_explicit, wfp_id, _MARKER)
        if policy is not _MARKER:
            if getattr(policy, '_isAWorkflowPolicy', 0):
                return policy
        return None

    security.declarePublic('isValidPolicyName')
    def isValidPolicyName(self, policy_id):
        """ Return True if a policy exist
        """
        return self.getWorkflowPolicyById(policy_id) is not None

    security.declareProtected(ManageWorkflowPolicies, 'getWorkflowPolicies')
    def getWorkflowPolicies(self):
        """ Return the list of workflow policies.
        """
        wfps = []
        for obj_name, obj in self.objectItems():
            if getattr(obj, '_isAWorkflowPolicy', 0):
                wfps.append(obj)
        return tuple(wfps)

    security.declarePublic('getWorkflowPolicyIds')
    def getWorkflowPolicyIds(self):
        """ Return the list of workflow policy ids.
        """
        wfp_ids = []

        for obj_id, obj in self.objectItems():
            if getattr(obj, '_isAWorkflowPolicy', 0):
                wfp_ids.append(obj_id)

        return tuple(wfp_ids)

    security.declarePublic('getWorkflowPolicyInfos')
    def getWorkflowPolicyInfos(self):
        """ Return the list of workflow policy ids.
        """
        wfp_ids = []
        for obj_id, obj in self.objectItems():
            if getattr(obj, '_isAWorkflowPolicy', 0):
                wfp_ids.append({'id': obj_id, 'title': obj.title_or_id(),
                                'description': obj.description})

        return tuple(wfp_ids)


    security.declareProtected( View, 'getWorkflowPolicyConfig')
    def getWorkflowPolicyConfig(self, ob):
        """ Return a local workflow configuration if it exist
        """
        if self.isSiteRoot(ob):
            # Site root use portal_workflow tool as local policy
            return None
        if not _checkPermission(ManageWorkflowPolicies, ob):
            raise Unauthorized("You need %s permission on %s" % (
               ManageWorkflowPolicies, '/'.join(ob.getPhysicalPath())))

        return getattr(ob.aq_explicit, WorkflowPolicyConfig_id, None)


    security.declareProtected( View, 'isSiteRoot')
    def isSiteRoot(self, ob):
        """ Returns a boolean value indicating if the object is an ISiteRoot
        or the default page of an ISiteRoot.
        """
        siteroot = ISiteRoot.providedBy(ob)
        if siteroot:
            return True
        parent = aq_parent(ob)
        if ISiteRoot.providedBy(parent):
            if (getattr(ob, 'isPrincipiaFolderish', False)
                and ob.isPrincipiaFolderish):
                # We are looking at a folder in the root
                return False
            # We are at a non-folderish item in the root
            return True
        return False

    def _post_init(self):
        """
        _post_init(self) => called from manage_add method, acquired within ZODB (__init__ is not)
        """
        pass

    #
    #   portal_workflow_policy implementation.
    #

    def getMaxChainLength(self):
        """Return the max workflow chain length"""
        max_chain_length = self.getProperty('max_chain_length')
        return max_chain_length

    def setMaxChainLength(self, max_chain_length):
        """Set the max workflow chain length"""
        safeEditProperty(self, 'max_chain_length', max_chain_length, data_type='int')

_workflow_policy_factories = {}

def _makeWorkflowPolicyFactoryKey(factory, id=None, title=None):
    # The factory should take one argument, id.
    if id is None:
        id = getattr(factory, 'id', '') or getattr(factory, 'meta_type', '')
    if title is None:
        title = getattr(factory, 'title', '')
    key = id
    if title:
        key = key + ' (%s)' % title
    return key

def addWorkflowPolicyFactory(factory, id=None, title=None):
    key = _makeWorkflowPolicyFactoryKey( factory, id, title )
    _workflow_policy_factories[key] = factory

def _removeWorkflowPolicyFactory( factory, id=None, title=None ):
    """ Make teardown in unitcase cleaner. """
    key = _makeWorkflowPolicyFactoryKey( factory, id, title )
    try:
        del _workflow_policy_factories[key]
    except KeyError:
        pass

InitializeClass(PlacefulWorkflowTool)
registerToolInterface('portal_placeful_workflow', IPlacefulWorkflowTool)
