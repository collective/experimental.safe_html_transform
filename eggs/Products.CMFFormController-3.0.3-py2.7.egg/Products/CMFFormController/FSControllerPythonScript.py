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

import copy
from zope.tales.tales import CompilerError

import Acquisition
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.Cache import Cacheable
from Products.CMFCore.DirectoryView import registerFileExtension, registerMetaType
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Script import FSPythonScript as BaseClass
from ControllerPythonScript import ControllerPythonScript
from ControllerState import ControllerState
from FSControllerBase import FSControllerBase
from utils import log, logException
from interfaces import IControllerPythonScript

from zope.interface import implements

class FSControllerPythonScript (FSControllerBase, BaseClass):
    """FSControllerPythonScripts act like Controller Python Scripts but are not
    directly modifiable from the management interface."""

    meta_type = 'Filesystem Controller Python Script'

    implements(IControllerPythonScript)

    manage_options=(
           (
            {'label':'Customize', 'action':'manage_main'},
            {'label':'Test', 'action':'ZScriptHTML_tryForm'},
            {'label':'Validation','action':'manage_formValidatorsForm'},
            {'label':'Actions','action':'manage_formActionsForm'},
           ) + Cacheable.manage_options)

    is_validator = 0

    # Use declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    def __init__(self, id, filepath, fullname=None, properties=None):
        BaseClass.__init__(self, id, filepath, fullname, properties)
        self.filepath = self._filepath = filepath  # add _filepath for compatibility with pending CMF patch
        try:
            self._read_action_metadata(self.getId(), filepath)
            self._read_validator_metadata(self.getId(), self.filepath)
        except (ValueError, CompilerError), e:
            log(summary='metadata error', text='file = %s' % filepath)
            raise


    def _updateFromFS(self):
        # workaround for Python 2.1 multiple inheritance lameness
        return self._baseUpdateFromFS()


    def _readMetadata(self):
        # workaround for Python 2.1 multiple inheritance lameness
        return self._baseReadMetadata()


    def _readFile(self, reparse):
        BaseClass._readFile(self, reparse)
        self._readMetadata()


    def __call__(self, *args, **kwargs):
        REQUEST = self.REQUEST
        controller = getToolByName(self, 'portal_form_controller')
        controller_state = controller.getState(self, is_validator=0)
        controller_state = self.getButton(controller_state, REQUEST)
        validators = self.getValidators(controller_state, REQUEST).getValidators()

        # put all arguments into a dict
        c = self.func_code
        param_names = c.co_varnames[:c.co_argcount]
        argdict = {}
        index = 0
        # grab the names for positional arguments out of the function code
        for a in args:
            argdict[param_names[index]] = a
            index += 1
        argdict.update(kwargs)

        controller_state = controller.validate(controller_state, REQUEST, validators, argdict)

        if controller_state.getStatus() == 'success':
            result = FSControllerPythonScript.inheritedAttribute('__call__')(self, *args, **kwargs)
            if getattr(result, '__class__', None) == ControllerState and not result._isValidating():
                return self.getNext(result, self.REQUEST)
            return result
        else:
            return self.getNext(controller_state, self.REQUEST)


    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, object, container):
        try:
            BaseClass.manage_afterAdd(self, object, container)
            # Re-read .metadata after adding so that we can do validation checks
            # using information in portal_form_controller.  Since manage_afterAdd
            # is not guaranteed to run, we also call these in __init__
            self._read_action_metadata(self.getId(), self.filepath)
            self._read_validator_metadata(self.getId(), self.filepath)
        except:
            log(summary='metadata error', text='file = %s' % self.filepath)
            logException()
            raise

    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        obj = ControllerPythonScript(self.getId(), filepath=self.filepath)
        obj.write(self.read())
        obj.validators = copy.copy(Acquisition.aq_base(self.validators))  # XXX - don't forget to enable this
        obj.actions = copy.copy(Acquisition.aq_base(self.actions))
        return obj


    security.declarePublic('writableDefaults')
    def writableDefaults(self):
        """Can default actions and validators be modified?"""
        return 0

    def _getState(self):
        return getToolByName(self, 'portal_form_controller').getState(self, is_validator=0)


InitializeClass(FSControllerPythonScript)


registerFileExtension('cpy', FSControllerPythonScript)
registerMetaType('Controller Python Script', FSControllerPythonScript)
