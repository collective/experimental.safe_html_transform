# -*- coding: utf-8 -*-
""" Zope 2 permissions
"""

from Products.CMFCore.permissions import setDefaultRoles

ManageWorkflowPolicies = 'CMFPlacefulWorkflow: Manage workflow policies'
setDefaultRoles(ManageWorkflowPolicies, ('Manager', 'Site Administrator'))
