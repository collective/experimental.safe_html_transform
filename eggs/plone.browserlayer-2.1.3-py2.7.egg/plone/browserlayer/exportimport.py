from zope.interface import implements

from zope.component import adapts
from zope.component import getSiteManager
from zope.component import queryMultiAdapter

from zope.component.interfaces import IComponentRegistry

from plone.browserlayer.interfaces import ILocalBrowserLayerType
from plone.browserlayer.utils import register_layer
from plone.browserlayer.utils import unregister_layer

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron

from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import _getDottedName
from Products.GenericSetup.utils import _resolveDottedName


def dummyGetId():
    return ''


class BrowserLayerXMLAdapter(XMLAdapterBase):
    """Im- and exporter for local browser layers
    """
    implements(IBody)
    adapts(IComponentRegistry, ISetupEnviron)

    name = 'browserlayer'
    _LOGGER_ID = 'browserlayer'

    def _exportNode(self):
        # hack around an issue where _getObjectNode expects to have the context
        # a meta_type and a getId method, which isn't the case for a component
        # registry
        if IComponentRegistry.providedBy(self.context):
            self.context.meta_type = 'ComponentRegistry'
            self.context.getId = dummyGetId
        node = self._getObjectNode('layers')
        if IComponentRegistry.providedBy(self.context):
            del(self.context.meta_type)
            del(self.context.getId)
        node.appendChild(self._extractLayers())
        self._logger.info('Browser layers exported')
        return node

    def _importNode(self, node):
        self._initProvider(node)
        self._logger.info('Browser layers imported')

    def _initProvider(self, node):
        if self.environ.shouldPurge():
            self._purgeLayers()
        self._initLayers(node)

    def _purgeLayers(self):
        registeredLayers = [r.name for r in self.context.registeredUtilities()
                            if r.provided == ILocalBrowserLayerType]
        for name in registeredLayers:
            unregister_layer(name, site_manager=self.context)

    def _initLayers(self, node):
        for child in node.childNodes:
            if child.nodeName.lower() == 'layer':
                name = child.getAttribute('name')
                if child.getAttribute('remove'):
                    try:
                        unregister_layer(name, site_manager=self.context)
                    except KeyError, e:
                        self._logger.info(e)
                    continue
                interface = _resolveDottedName(child.getAttribute('interface'))
                register_layer(interface, name, site_manager=self.context)

    def _extractLayers(self):
        fragment = self._doc.createDocumentFragment()

        registrations = [r for r in self.context.registeredUtilities()
                            if r.provided == ILocalBrowserLayerType]

        registrations.sort()

        for r in registrations:
            child = self._doc.createElement('layer')
            child.setAttribute('name', r.name)
            child.setAttribute('interface', _getDottedName(r.component))
            fragment.appendChild(child)

        return fragment


def importLayers(context):
    """Import local browser layers
    """
    sm = getSiteManager(context.getSite())
    if sm is None or not IComponentRegistry.providedBy(sm):
        logger = context.getLogger('browserlayer')
        logger.info("Can not register components - no site manager found.")
        return

    importer = queryMultiAdapter((sm, context), IBody,
                                 name=u'plone.browserlayer')
    if importer is not None:
        filename = '%s%s' % (importer.name, importer.suffix)
        body = context.readDataFile(filename)
        if body is not None:
            importer.filename = filename  # for error reporting
            importer.body = body


def exportLayers(context):
    """Export local browser layers
    """
    sm = getSiteManager(context.getSite())
    if sm is None or not IComponentRegistry.providedBy(sm):
        logger = context.getLogger('browserlayer')
        logger.info("Can not register components - no site manager found.")
        return

    exporter = queryMultiAdapter((sm, context), IBody,
                                 name=u'plone.browserlayer')
    if exporter is not None:
        filename = '%s%s' % (exporter.name, exporter.suffix)
        body = exporter.body
        if body is not None:
            context.writeDataFile(filename, body, exporter.mime_type)
