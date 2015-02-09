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
##########################################################################
"""Zope object encapsulating a controlled page templates that comes from the
   filesystem.
"""

import os
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as BaseClass
from Products.PageTemplates.TALES import CompilerError
from BaseControllerPageTemplate import BaseControllerPageTemplate
from FSControllerBase import FSControllerBase
from utils import log, logException


class ControllerPageTemplateFile(BaseClass, BaseControllerPageTemplate, FSControllerBase):
    """Wrapper for Controller Page Template"""

    meta_type = 'Controller Page Template (File)'

    manage_options=(
        ({'label':'Customize', 'action':'manage_main'},
         {'label':'Test', 'action':'ZScriptHTML_tryForm'},
         {'label':'Validation','action':'manage_formValidatorsForm'},
         {'label':'Actions','action':'manage_formActionsForm'},
        ))

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    def __init__(self, filename, _prefix=None, **kw):
        filename = os.path.normpath(filename)
        if not os.path.splitext(filename)[1]:
            filename = filename + '.cpt'
        retval = ControllerPageTemplateFile.inheritedAttribute('__init__')(self, filename, _prefix, **kw)

        self.id = os.path.splitext(os.path.basename(filename))[0]
        self.filepath = self.filename
        try:
            self._read_action_metadata(self.getId(), self.filepath)
            self._read_validator_metadata(self.getId(), self.filepath)
            return retval
        except (ValueError, CompilerError), e:
            log(summary='metadata error', text='file = %s' % self.filepath)
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


    def __call__(self, *args, **kwargs):
        return self._call(ControllerPageTemplateFile.inheritedAttribute('__call__'), *args, **kwargs)


    security.declarePublic('writableDefaults')
    def writableDefaults(self):
        """Can default actions and validators be modified?"""
        return 0
