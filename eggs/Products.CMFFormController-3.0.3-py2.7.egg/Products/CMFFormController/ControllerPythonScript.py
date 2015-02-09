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

import os, re
from App.Common import package_home
import AccessControl
from OFS.SimpleItem import SimpleItem
from urllib import quote
from Shared.DC.Scripts.Script import BindingsUI
from OFS.History import Historical
from OFS.Cache import Cacheable
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.utils import getToolByName
from Script import PythonScript as BaseClass
from ControllerBase import ControllerBase
from ControllerState import ControllerState
from FormAction import FormActionContainer
from FormValidator import FormValidatorContainer
from interfaces import IControllerPythonScript

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
                             'www', 'default_cpy')

_marker = []  # Create a new marker object


_first_indent = re.compile('(?m)^ *(?! |$)')
_nonempty_line = re.compile('(?m)^(.*\S.*)$')

# ###########################################################################
# Product registration and Add support
manage_addControllerPythonScriptForm = PageTemplateFile('www/cpyAdd', globals())
manage_addControllerPythonScriptForm.__name__='manage_addControllerPythonScriptForm'

def manage_addControllerPythonScript(self, id, REQUEST=None, submit=None):
    """Add a Python script to a folder.
    """
    id = str(id)
    id = self._setObject(id, ControllerPythonScript(id))
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


class ControllerPythonScript(BaseClass, ControllerBase):
    """Web-callable scripts written in a safe subset of Python.

    The function may include standard python code, so long as it does
    not attempt to use the "exec" statement or certain restricted builtins.
    """

    meta_type='Controller Python Script'

    implements(IControllerPythonScript)

    manage_options = (
        {'label':'Edit',
         'action':'ZPythonScriptHTML_editForm',
         'help': ('PythonScripts', 'PythonScript_edit.stx')},
        ) + BindingsUI.manage_options + (
        {'label':'Test',
         'action':'ZScriptHTML_tryForm',
         'help': ('PythonScripts', 'PythonScript_test.stx')},
        {'label':'Validation',
         'action':'manage_formValidatorsForm'},
        {'label':'Actions',
         'action':'manage_formActionsForm'},
        {'label':'Proxy',
         'action':'manage_proxyForm',
         'help': ('OFSP','DTML-DocumentOrMethod_Proxy.stx')},
        ) + Historical.manage_options + SimpleItem.manage_options + \
        Cacheable.manage_options

    is_validator = 0

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
        self.validators = FormValidatorContainer()
        self.actions = FormActionContainer()
        return ControllerPythonScript.inheritedAttribute('__init__')(self, *args, **kwargs)


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
            result = ControllerPythonScript.inheritedAttribute('__call__')(self, *args, **kwargs)
            if getattr(result, '__class__', None) == ControllerState and not result._isValidating():
                return self.getNext(result, self.REQUEST)
            return result
        else:
            return self.getNext(controller_state, self.REQUEST)


    def _getState(self):
        return getToolByName(self, 'portal_form_controller').getState(self, is_validator=0)


    def _notifyOfCopyTo(self, container, op=0):
        # BaseClass.inheritedAttribute('notifyOfCopyTo')(self, container, op)
        self._base_notifyOfCopyTo(container, op)

    def manage_afterAdd(self, object, container):
        BaseClass.inheritedAttribute('manage_afterAdd')(self, object, container)
        self._base_manage_afterAdd(object, container)

    def manage_afterClone(self, object):
        BaseClass.inheritedAttribute('manage_afterClone')(self, object)
        self._base_manage_afterClone(object)
