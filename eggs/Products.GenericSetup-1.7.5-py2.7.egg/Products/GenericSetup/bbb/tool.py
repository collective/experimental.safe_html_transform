##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Classes:  SetupTool
"""

from Products.GenericSetup.tool import exportStepRegistries
from Products.GenericSetup.tool import importToolset
from Products.GenericSetup.tool import exportToolset
from Products.GenericSetup.tool import SetupTool as BaseTool


class SetupTool(BaseTool):

    #BBB: for setup tools created with CMF 1.5
    id = 'portal_setup'

    def __init__(self, id='portal_setup'):
        BaseTool.__init__(self, id)
