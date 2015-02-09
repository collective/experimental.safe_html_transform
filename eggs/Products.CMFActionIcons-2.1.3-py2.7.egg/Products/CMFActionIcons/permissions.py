##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFActionIcons product permissions.

$Id: permissions.py 110650 2010-04-08 15:30:52Z tseaver $
"""
from AccessControl import ModuleSecurityInfo

security = ModuleSecurityInfo('Products.CMFActionIcons.permissions')

security.declarePublic('ManagePortal')
from Products.CMFCore.permissions import ManagePortal

security.declarePublic('View')
from Products.CMFCore.permissions import View
