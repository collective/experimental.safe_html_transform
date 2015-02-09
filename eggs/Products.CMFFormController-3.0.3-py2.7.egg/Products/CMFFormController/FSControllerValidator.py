##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
# THIS FILE CONTAINS MODIFIED CODE FROM ZOPE 2.6.2
##############################################################################
""" Customizable controlled python scripts that come from the filesystem.
"""

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.Cache import Cacheable
from Products.CMFCore.DirectoryView import registerFileExtension, registerMetaType
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Script import FSPythonScript as BaseClass
from ControllerValidator import ControllerValidator
from ControllerBase import ControllerBase
from utils import logException
from interfaces import IControllerValidator

from zope.interface import implements

class FSControllerValidator (BaseClass, ControllerBase):
    """FSControllerValidators act like Controller Python Scripts but are not
    directly modifiable from the management interface."""

    meta_type = 'Filesystem Controller Validator'

    implements(IControllerValidator)

    manage_options=(
           (
            {'label':'Customize', 'action':'manage_main'},
            {'label':'Test', 'action':'ZScriptHTML_tryForm'},
           ) + Cacheable.manage_options)

    is_validator = 1

    # Use declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    def __init__(self, id, filepath, fullname=None, properties=None):
        BaseClass.__init__(self, id, filepath, fullname, properties)
        self.filepath = filepath
        self._read_action_metadata(self.getId(), filepath)


    def __call__(self, *args, **kwargs):
        result = FSControllerValidator.inheritedAttribute('__call__')(self, *args, **kwargs)
        return result


    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, object, container):
        try:
            BaseClass.manage_afterAdd(self, object, container)
        except:
            logException()
            raise


    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        obj = ControllerValidator(self.getId())
        obj.write(self.read())
        return obj


    security.declarePublic('writableDefaults')
    def writableDefaults(self):
        """Can default actions and validators be modified?"""
        return 0

    def _getState(self):
        return getToolByName(self, 'portal_form_controller').getState(self, is_validator=1)

InitializeClass(FSControllerValidator)

registerFileExtension('vpy', FSControllerValidator)
registerMetaType('Controller Validator', FSControllerValidator)
