from Products.ATContentTypes.interfaces import IATCTTool
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.CMFCore.utils import getToolByName


def safeGetAttribute(node, attribute):
    """Get an attribute froma node, but return None if it does not exist.
    """
    if not node.hasAttribute(attribute):
        return None
    else:
        return node.getAttribute(attribute)


class ATCTToolXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):
    """Node in- and exporter for ATCTTool.
    """
    __used_for__ = IATCTTool

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._doc.createElement('atcttool')
        node.appendChild(self._extractSettings())
        node.appendChild(self._extractProperties())

        self._logger.info('ATCTTool settings exported.')
        return node

    def _importNode(self, node):
        purge = self.environ.shouldPurge()
        if node.getAttribute('purge'):
            purge = self._convertToBoolean(node.getAttribute('purge'))

        if purge:
            self._purgeSettings()
            self._purgeProperties()

        self._initSettings(node)
        self._initProperties(node)
        self._logger.info('ATCTTool settings imported.')

    def _purgeSettings(self):
        # initialize topic tool
        self.context.topic_indexes = {}
        self.context.topic_metadata = {}
        self.context.allowed_portal_types = []
        self.context.createInitialIndexes()
        self.context.createInitialMetadata()

    def _initSettings(self, node):
        for child in node.childNodes:
            if child.nodeName == 'topic_indexes':
                for indexNode in child.childNodes:
                    if indexNode.nodeName == 'index':
                        name = indexNode.getAttribute('name')
                        if indexNode.hasAttribute("remove"):
                            self.context.removeIndex(name)
                            continue

                        try:
                            self.context.getIndex(name)
                        except AttributeError:
                            self.context.addIndex(name)

                        description = safeGetAttribute(indexNode, 'description')
                        enabled = safeGetAttribute(indexNode, 'enabled')
                        if enabled is not None:
                            enabled = self._convertToBoolean(enabled)
                        friendlyName = safeGetAttribute(indexNode, 'friendlyName')

                        criteria = None
                        for critNode in indexNode.childNodes:
                            if critNode.nodeName == 'criteria':
                                for textNode in critNode.childNodes:
                                    if textNode.nodeName != '#text' or \
                                        not textNode.nodeValue.strip():
                                        continue
                                    if criteria is None:
                                        criteria = []
                                    criteria.append(str(textNode.nodeValue))

                        self.context.updateIndex(name,
                                              friendlyName=friendlyName,
                                              description=description,
                                              enabled=enabled,
                                              criteria=criteria)

            if child.nodeName == 'topic_metadata':
                for metadataNode in child.childNodes:
                    if metadataNode.nodeName == 'metadata':
                        name = metadataNode.getAttribute('name')
                        if metadataNode.hasAttribute("remove"):
                            self.context.removeMetadata(name)
                            continue

                        try:
                            self.context.getMetadata(name)
                        except AttributeError:
                            self.context.addMetadata(name)

                        description = safeGetAttribute(metadataNode, 'description')
                        enabled = safeGetAttribute(metadataNode, 'enabled')
                        if enabled is not None:
                            enabled = self._convertToBoolean(enabled)
                        friendlyName = safeGetAttribute(metadataNode, 'friendlyName')
                        self.context.updateMetadata(name,
                                                 friendlyName=friendlyName,
                                                 description=description,
                                                 enabled=enabled)

    def _extractSettings(self):
        fragment = self._doc.createDocumentFragment()
        # topic tool indexes
        indexes = self._doc.createElement('topic_indexes')
        for indexname in self.context.getIndexes():
            index = self.context.getIndex(indexname)
            child = self._doc.createElement('index')
            child.setAttribute('name', str(indexname))
            child.setAttribute('friendlyName', str(index.friendlyName))
            child.setAttribute('description', str(index.description))
            child.setAttribute('enabled', str(bool(index.enabled)))
            for criteria in index.criteria:
                if criteria != 'criterion':
                    sub = self._doc.createElement('criteria')
                    sub.appendChild(self._doc.createTextNode(criteria))
                    child.appendChild(sub)
            indexes.appendChild(child)
        fragment.appendChild(indexes)
        # topic tool metadata
        metadata = self._doc.createElement('topic_metadata')
        for metaname in self.context.getAllMetadata():
            meta = self.context.getMetadata(metaname)
            child = self._doc.createElement('metadata')
            child.setAttribute('name', str(metaname))
            child.setAttribute('friendlyName', str(meta.friendlyName))
            child.setAttribute('description', str(meta.description))
            child.setAttribute('enabled', str(bool(meta.enabled)))
            metadata.appendChild(child)
        fragment.appendChild(metadata)

        return fragment


def importATCTTool(context):
    """Import ATCT Tool configuration.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_atct', None)

    if tool is not None:
        importObjects(tool, '', context)


def exportATCTTool(context):
    """Export ATCT Tool configuration.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_atct', None)
    if tool is None:
        logger = context.getLogger("atcttool")
        logger.info("Nothing to export.")
        return

    exportObjects(tool, '', context)
