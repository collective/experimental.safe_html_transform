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

"""Controller Python Scripts Product

This product provides support for Script objects containing restricted
Python code.
"""

import os
from App.Common import package_home
import AccessControl
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.SimpleItem import SimpleItem
from urllib import quote
from Shared.DC.Scripts.Script import BindingsUI
from OFS.History import Historical
from OFS.Cache import Cacheable
from Products.CMFCore.utils import getToolByName
from Script import PythonScript as BaseClass
from ControllerBase import ControllerBase
from interfaces import IControllerValidator

from zope.interface import implements

# Track the Python bytecode version
import imp
Python_magic = imp.get_magic()
del imp

# This should only be incremented to force recompilation.
Script_magic = 3
_log_complaint = (
    'Some of your Scripts have stale code cached.  Since Zope cannot'
    ' use this code, startup will be slightly slower until these Scripts'
    ' are edited. You can automatically recompile all Scripts that have'
    ' this problem by visiting /manage_addProduct/PythonScripts/recompile'
    ' of your server in a browser.')

_default_file = os.path.join(package_home(globals()),
                             'www', 'default_vpy')

_marker = []  # Create a new marker object

# ###########################################################################
# Product registration and Add support
manage_addControllerValidatorForm = PageTemplateFile('www/vpyAdd', globals())
manage_addControllerValidatorForm.__name__='manage_addControllerValidatorForm'

def manage_addControllerValidator(self, id, REQUEST=None, submit=None):
    """Add a Python script to a folder.
    """
    id = str(id)
    id = self._setObject(id, ControllerValidator(id))
    if REQUEST is not None:
        file = REQUEST.form.get('file', '')
        if not isinstance(file, str):
            file = file.read()
        if not file:
            file = open(_default_file).read()
        self._getOb(id).write(file)
        try: u = self.DestinationURL()
        except: u = REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''


class ControllerValidator(BaseClass, ControllerBase):
    """Web-callable scripts written in a safe subset of Python.

    The function may include standard python code, so long as it does
    not attempt to use the "exec" statement or certain restricted builtins.
    """

    meta_type='Controller Validator'

    implements(IControllerValidator)

    manage_options = (
        {'label':'Edit',
         'action':'ZPythonScriptHTML_editForm',
         'help': ('PythonScripts', 'PythonScript_edit.stx')},
        ) + BindingsUI.manage_options + (
        {'label':'Test',
         'action':'ZScriptHTML_tryForm',
         'help': ('PythonScripts', 'PythonScript_test.stx')},
#        {'label':'Actions','action':'manage_formActionsForm'},
        {'label':'Proxy',
         'action':'manage_proxyForm',
         'help': ('OFSP','DTML-DocumentOrMethod_Proxy.stx')},
        ) + Historical.manage_options + SimpleItem.manage_options + \
        Cacheable.manage_options

    is_validator = 1

    security = AccessControl.ClassSecurityInfo()
    security.declareObjectProtected('View')

    security.declareProtected('View', '__call__')

    security.declareProtected('View management screens',
      'ZPythonScriptHTML_editForm', 'manage_main', 'read',
      'ZScriptHTML_tryForm', 'PrincipiaSearchSource',
      'document_src', 'params', 'body')

    security.declareProtected('Change Python Scripts',
      'ZPythonScriptHTML_editAction',
      'ZPythonScript_setTitle', 'ZPythonScript_edit',
      'ZPythonScriptHTML_upload', 'ZPythonScriptHTML_changePrefs')


    def __init__(self, *args, **kwargs):
#        self.actions = FormActionContainer()
        return ControllerValidator.inheritedAttribute('__init__')(self, *args, **kwargs)


    def __call__(self, *args, **kwargs):
        result = ControllerValidator.inheritedAttribute('__call__')(self, *args, **kwargs)
#        if getattr(result, '__class__', None) == ControllerState and not result._isValidating():
#            return self.getNext(result, self.REQUEST)
        return result

    def _getState(self):
        return getToolByName(self, 'portal_form_controller').getState(self, is_validator=1)

    def _notifyOfCopyTo(self, container, op=0):
        # BaseClass.inheritedAttribute('notifyOfCopyTo')(self, container, op)
        self._base_notifyOfCopyTo(container, op)

    def manage_afterAdd(self, object, container):
        BaseClass.inheritedAttribute('manage_afterAdd')(self, object, container)
        self._base_manage_afterAdd(object, container)

    def manage_afterClone(self, object):
        BaseClass.inheritedAttribute('manage_afterClone')(self, object)
        self._base_manage_afterClone(object)
