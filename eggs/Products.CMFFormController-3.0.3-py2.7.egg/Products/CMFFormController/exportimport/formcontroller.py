##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""CMFFormController setup handlers.

$Id$
"""

import os
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.Common import package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal

from Products.GenericSetup.utils import DEFAULT, KEY
from Products.GenericSetup.utils import ImportConfiguratorBase, ExportConfiguratorBase

_pkgdir = package_home( globals() )
_xmldir = os.path.join( _pkgdir, 'xml' )

from Products.CMFFormController.FormAction import FormAction
from Products.CMFFormController.FormValidator import FormValidator

#
#   Configurator entry points
#
_FILENAME = 'cmfformcontroller.xml'

def importCMFFormController(context):
    """ Import CMFFormController settings from an XML file.
    """
    site = context.getSite()
    fc = getToolByName(site, 'portal_form_controller', None)
    if fc is None:
        return 'CMFFormController: No tool!'

    body = context.readDataFile(_FILENAME)
    if body is None:
        return 'CMFFormController: Nothing to import.'

    if context.shouldPurge():
        fc.__init__()

    # now act on the settings we've retrieved
    configurator = CMFFormControllerImportConfigurator(site)
    fc_info = configurator.parseXML(body)

    for validator in fc_info['validators']:
        fc.validators.set(FormValidator(validator['object_id'],
                                        validator.get('context_type', ''),
                                        validator.get('button', ''),
                                        str(validator['validators']).split(',')))
    for action in fc_info['actions']:
        fc.actions.set(FormAction(action['object_id'],
                                  action['status'],
                                  action.get('context_type', ''),
                                  action.get('button', ''),
                                  action['action_type'],
                                  str(action['action_arg'])))

    return 'CMFFormController settings imported.'

def exportCMFFormController(context):
    """ Export CMFFormController settings as an XML file.
    """
    site = context.getSite()

    fc = getToolByName(site, 'portal_form_controller', None)
    if fc is None:
        return 'CMFFormController: Nothing to export.'

    fcc = CMFFormControllerExportConfigurator( site ).__of__( site )
    text = fcc.generateXML()

    context.writeDataFile( _FILENAME, text, 'text/xml' )

    return 'CMFFormController settings exported.'


class CMFFormControllerExportConfigurator(ExportConfiguratorBase):
    """ Synthesize XML description of CMFFormController properties.
    """
    security = ClassSecurityInfo()

    security.declareProtected( ManagePortal, 'listValidators' )
    def listValidators(self):
        """ Return a list of mappings describing the tool's validators.
        """
        fc = getToolByName(self._site, 'portal_form_controller')

        for validator in fc.listFormValidators():
            yield {'object_id': validator.getObjectId(),
                   'context_type': validator.getContextType(),
                   'button': validator.getButton(),
                   'validators': validator.getValidators(),
                  }

    def listActions(self):
        """ Return a list of mappings describing the tool's actions.
        """
        fc = getToolByName(self._site, 'portal_form_controller')

        for action in fc.listFormActions():
            yield {'object_id': action.getObjectId(),
                   'status': action.getStatus(),
                   'context_type': action.getContextType(),
                   'button': action.getButton(),
                   'action_type': action.getActionType(),
                   'action_arg': action.getActionArg()
                  }

    security.declarePrivate('_getExportTemplate')
    def _getExportTemplate(self):

        return PageTemplateFile('fcExport.xml', _xmldir)

InitializeClass(CMFFormControllerExportConfigurator)

class CMFFormControllerImportConfigurator(ImportConfiguratorBase):

    def _getImportMapping(self):
        # Each key represents the name of an xml node
        # 'cmfformcontroller' is the top level node
        # It will contain nodes of type 'action' and 'validator';
        # 'action' and 'validator' nodes will be stored in the
        # dict generated by import in tuples with keys 'actions'
        # and 'validators', respectively
        return {
          'cmfformcontroller': {
            'action':     {KEY: 'actions', DEFAULT: ()},
            'validator':  {KEY: 'validators', DEFAULT: ()},
          },
          'action':
             { 'object_id':    {},
               'status':       {},
               'context_type': {},
               'button':       {},
               'action_type':  {},
               'action_arg':   {},
             },
          'validator':
             { 'object_id':    {},
               'context_type': {},
               'button':       {},
               'validators':   {},
             }
          }

InitializeClass(CMFFormControllerImportConfigurator)
