# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
$Id: config.py 7851 2007-03-31 13:01:43Z seletz $
"""

from StringIO import StringIO

from zope.interface import implements

from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter
from Products.GenericSetup.content import FauxDAVRequest
from Products.GenericSetup.content import FauxDAVResponse
from Products.GenericSetup.utils import ExportConfiguratorBase
from Products.GenericSetup.utils import ImportConfiguratorBase
from Products.GenericSetup.utils import _getDottedName
from Products.GenericSetup.utils import _resolveDottedName
from Products.GenericSetup.utils import CONVERTER
from Products.GenericSetup.utils import DEFAULT
from Products.GenericSetup.utils import KEY
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.Marshall.config import TOOL_ID
from Products.Marshall.registry import createPredicate

_FILENAME = 'marshall-registry.xml'


def _getRegistry(site):
    registry = site._getOb(TOOL_ID, None)

    if registry is None:
        raise ValueError('Marshall Registry Not Found')

    return registry


def exportMarshallRegistry(context):
    """ Export marshall registry as an XML file.

    o Designed for use as a GenericSetup export step.
    """
    registry = _getRegistry(context.getSite())
    exporter = MarshallRegistryExporter(registry).__of__(registry)
    xml = exporter.generateXML()
    context.writeDataFile(_FILENAME, xml, 'text/xml')
    return 'Marshall Registry exported.'


def _updateMarshallRegistry(registry, xml, should_purge, encoding=None):

    if should_purge:

        registry.manage_delObjects(ids=list(registry.objectIds()))

    importer = MarshallRegistryImporter(registry, encoding)
    reg_info = importer.parseXML(xml)

    for info in reg_info['predicates']:
        if registry.hasObject(info['id']):
            registry.manage_delObjects(ids=[info['id']])
        obj = createPredicate(info['predicate_name'],
                              info['id'], info['title'],
                              info['expression'],
                              info['component'])
        if (info['predicate_name'] in ('xmlns_attr',) and
            info.get('xml_settings', ())):
            obj.edit(**info['xml_settings'][0])
        registry._setObject(info['id'], obj)


def importMarshallRegistry(context):
    """ Import marshall registry from an XML file.

    o Designed for use as a GenericSetup import step.
    """
    registry = _getRegistry(context.getSite())
    encoding = context.getEncoding()

    xml = context.readDataFile(_FILENAME)
    if xml is None:
        return 'Site properties: Nothing to import.'

    _updateMarshallRegistry(registry, xml, context.shouldPurge(), encoding)
    return 'Marshall Registry imported.'


class MarshallRegistryExporter(ExportConfiguratorBase):

    def __init__(self, context, encoding='utf-8'):
        ExportConfiguratorBase.__init__(self, None, encoding)
        self.context = context

    def _getExportTemplate(self):
        return PageTemplateFile('xml/mrExport.xml', globals())

    def listPredicates(self):
        for predicate in self.context.objectValues():
            info = {}
            info['id'] = predicate.getId()
            info['title'] = predicate.title_or_id()
            info['expression'] = predicate.getExpression()
            info['component'] = predicate.getComponentName()
            info['predicate_name'] = predicate.getPredicateName()
            if info['predicate_name'] in ('xmlns_attr',):
                info['xml_settings'] = settings = {}
                settings['element_name'] = predicate.getElementName()
                settings['element_ns'] = predicate.getElementNS()
                settings['attr_name'] = predicate.getAttributeName()
                settings['attr_ns'] = predicate.getAttributeNS()
                settings['value'] = predicate.getValue()
            yield info


class MarshallRegistryImporter(ImportConfiguratorBase):

    def __init__(self, context, encoding=None):
        ImportConfiguratorBase.__init__(self, None, encoding)
        self.context = context

    def _getImportMapping(self):

        return {
          'marshall-registry':
              {'predicate':        {KEY: 'predicates', DEFAULT: ()},
               },
          'predicate':
              {'id':               {KEY: 'id'},
               'title':            {KEY: 'title'},
               'expression':       {KEY: 'expression'},
               'component':        {KEY: 'component'},
               'predicate_name':   {KEY: 'predicate_name'},
               'xml-settings':     {KEY: 'xml_settings', DEFAULT: ()}
               },
          'xml-settings':
              {'element-name':   {KEY: 'element_name'},
               'element-ns':     {KEY: 'element_ns'},
               'attr-name':      {KEY: 'attr_name'},
               'attr-ns':        {KEY: 'attr_ns'},
               'value':          {KEY: 'value'}
               },
         }


class MarshallRegistryFileExportImportAdapter(object):
    """ Designed for use when exporting / importing within a container.
    """
    implements(IFilesystemExporter, IFilesystemImporter)

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        context = self.context
        exporter = MarshallRegistryExporter(context).__of__(context)
        xml = exporter.generateXML()
        export_context.writeDataFile(_FILENAME,
                                     xml,
                                     'text/xml',
                                     subdir,
                                    )

    def listExportableItems(self):
        """ See IFilesystemExporter.
        """
        return ()

    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter.
        """
        data = import_context.readDataFile(_FILENAME, subdir)
        if data is None:
            import_context.note('SGAIFA',
                                'no %s in %s' % (_FILENAME, subdir))
        else:
            request = FauxDAVRequest(BODY=data, BODYFILE=StringIO(data))
            response = FauxDAVResponse()
            _updatePluginRegistry(self.context,
                                  data,
                                  import_context.shouldPurge(),
                                  import_context.getEncoding(),
                                 )
