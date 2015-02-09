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
"""Cookie crumbler xml adapters and setup handlers. """

from zope.component import adapts

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase

from Products.CMFCore.interfaces import ICookieCrumbler
from Products.CMFCore.utils import getToolByName


class CookieCrumblerXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):

    """XML im- and exporter for CookieCrumbler.
    """

    adapts(ICookieCrumbler, ISetupEnviron)

    _LOGGER_ID = 'cookies'

    name = 'cookieauth'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())

        self._logger.info('Cookie crumbler exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()

        self._initProperties(node)

        self._logger.info('Cookie crumbler imported.')


def importCookieCrumbler(context):
    """Import cookie crumbler settings from an XML file.
    """
    site = context.getSite()
    tool = getToolByName(site, 'cookie_authentication', None)
    if tool is None:
        logger = context.getLogger('cookies')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)

def exportCookieCrumbler(context):
    """Export cookie crumbler settings as an XML file.
    """
    site = context.getSite()
    tool = getToolByName(site, 'cookie_authentication', None)
    if tool is None:
        logger = context.getLogger('cookies')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
