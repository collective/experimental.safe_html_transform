##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ActionIconsTool setup handlers.

$Id: exportimport.py 110650 2010-04-08 15:30:52Z tseaver $
"""

import os

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.Common import package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.component import getSiteManager

from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFActionIcons.permissions import ManagePortal
from Products.GenericSetup.utils import CONVERTER
from Products.GenericSetup.utils import DEFAULT
from Products.GenericSetup.utils import ExportConfiguratorBase
from Products.GenericSetup.utils import ImportConfiguratorBase
from Products.GenericSetup.utils import KEY

_pkgdir = package_home( globals() )
_xmldir = os.path.join( _pkgdir, 'xml' )

#
#   Configurator entry points
#
_FILENAME = 'actionicons.xml'

def importActionIconsTool(context):
    """ Import action icons tool settings from an XML file.
    """
    site = context.getSite()
    logger = context.getLogger('action-icons')

    body = context.readDataFile(_FILENAME)
    if body is None:
        logger.debug('Nothing to import.')
        return

    sm = getSiteManager(site)
    ait = sm.queryUtility(IActionIconsTool)
    if ait is None:
        logger.warning('No tool!')
        return

    if context.shouldPurge():
        ait.clearActionIcons()

    # now act on the settings we've retrieved
    configurator = ActionIconsToolImportConfigurator(site)
    ait_info = configurator.parseXML(body)

    for action_icon in ait_info['action_icons']:
        category = action_icon['category']
        action_id = action_icon['action_id']
        # Ignore the i18n markup
        if action_icon.get('i18n:attributes', None) is not None:
            del action_icon['i18n:attributes']
        if ait.queryActionInfo(category, action_id) is not None:
            ait.updateActionIcon(**action_icon)
        else:
            ait.addActionIcon(**action_icon)
    logger.info('Action icons tool settings imported.')

def exportActionIconsTool(context):
    """ Export caching policy manager settings as an XML file.
    """
    site = context.getSite()
    logger = context.getLogger('action-icons')

    tool = getSiteManager(site).queryUtility(IActionIconsTool)
    if tool is None:
        logger.debug('Nothing to export.')
        return

    mhc = ActionIconsToolExportConfigurator( site ).__of__( site )
    text = mhc.generateXML()

    context.writeDataFile( _FILENAME, text, 'text/xml' )
    logger.info('Action icons tool settings exported.')


class ActionIconsToolExportConfigurator(ExportConfiguratorBase):
    """ Synthesize XML description of cc properties.
    """
    security = ClassSecurityInfo()

    security.declareProtected( ManagePortal, 'listActionIconInfo' )
    def listActionIconInfo(self):
        """ Return a list of mappings describing the action icons.
        """
        sm = getSiteManager(self._site)
        ait = sm.getUtility(IActionIconsTool)
        for action_icon in ait.listActionIcons():
            yield {'category': action_icon.getCategory(),
                   'action_id': action_icon.getActionId(),
                   'title': action_icon.getTitle(),
                   'priority': action_icon.getPriority(),
                   'icon_expr': action_icon.getExpression(),
                  }

    security.declarePrivate('_getExportTemplate')
    def _getExportTemplate(self):

        return PageTemplateFile('aitExport.xml', _xmldir)

InitializeClass(ActionIconsToolExportConfigurator)


class ActionIconsToolImportConfigurator(ImportConfiguratorBase):

    def _getImportMapping(self):
        return {
          'action-icons':
             { 'action-icon': {KEY: 'action_icons', DEFAULT: ()},
               'i18n:domain': {},
               'xmlns:i18n': {},
             },
          'action-icon':
             { 'category': {},
               'action_id': {},
               'title': {},
               'icon_expr': {},
               'priority': {CONVERTER: self._convertToInteger},
               'i18n:attributes': {},
             },
          }

    def _convertToInteger(self, val):
        return int(val.strip())

InitializeClass(ActionIconsToolImportConfigurator)
