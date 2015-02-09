from persistent import Persistent
from zope.interface import implements

from plone.app.workflow.interfaces import ISharingPageRole

from zope.component import adapts
from zope.component import getSiteManager
from zope.component import queryMultiAdapter
from zope.component.interfaces import IComponentRegistry

from zope.dottedname.resolve import resolve

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import XMLAdapterBase

from zope.i18nmessageid import MessageFactory
PMF = MessageFactory('plone')


class PersistentSharingPageRole(Persistent):
    """These are registered as local utilities when managing the sharing
    page roles.
    """
    implements(ISharingPageRole)

    title = u""
    required_permission = None
    required_interface = None

    def __init__(self, title=u"",
                 required_permission=None, required_interface=None):
        self.title = PMF(title)
        self.required_permission = required_permission
        self.required_interface = required_interface


class SharingXMLAdapter(XMLAdapterBase):
    adapts(IComponentRegistry, ISetupEnviron)

    _LOGGER_ID = 'plone.app.workflow'

    name = 'plone.app.workflow.sharing'
    info_tag = u"__sharing_gs__"

    def _importNode(self, node):

        if self.environ.shouldPurge():
            self._purgeRoles()

        for child in node.childNodes:
            self._initRole(child)

    def _exportNode(self):
        regs = []
        for reg in self._iterRoleRegistrations():
            regs.append(self._extractRole(reg))

        node = self._doc.createElement('sharing')
        def _sort(key):
            return (key.getAttribute('id'), key.getAttribute('title'))
        regs.sort(key=_sort)
        for reg in regs:
            node.appendChild(reg)
        return node

    def _iterRoleRegistrations(self):
        for reg in tuple(self.context.registeredUtilities()):
            if reg.provided.isOrExtends(ISharingPageRole) \
                    and isinstance(reg.info, basestring)  \
                    and self.info_tag in reg.info:
                yield reg

    def _purgeRoles(self):
        for reg in self._iterRoleRegistrations():
            self.context.unregisterUtility(provided=reg.provided, name=reg.name)

    def _initRole(self, node):

        if node.nodeName != 'role':
            return

        name = unicode(node.getAttribute('id'))
        title = unicode(node.getAttribute('title'))
        required = node.getAttribute('permission') or None
        iface = node.getAttribute('interface') or None
        if iface is not None:
            iface = resolve(iface)

        if node.hasAttribute('remove'):
            utility = self.context.queryUtility(ISharingPageRole, name)
            if utility is not None:
                if name in self.context.objectIds():
                    self.context._delObject(name, suppress_events=True)
                self.context.unregisterUtility(utility, ISharingPageRole, name)
            return

        component = PersistentSharingPageRole(
            title=title, required_permission=required, required_interface=iface)

        self.context.registerUtility(component, ISharingPageRole, name, info=self.info_tag)

    def _extractRole(self, reg):

        component = reg.component

        node = self._doc.createElement('role')
        node.setAttribute('id', reg.name)
        node.setAttribute('title', component.title)

        if component.required_permission:
            node.setAttribute('permission', component.required_permission)

        if component.required_interface:
            iface = component.required_interface
            iface = iface.__module__ + '.' + iface.__name__
            node.setAttribute('interface', iface)

        return node


def import_sharing(context):

    sm = getSiteManager(context.getSite())
    logger = context.getLogger('plone.app.workflow')

    if sm is None or not IComponentRegistry.providedBy(sm):
        logger.info("Can not register sharing page roles, as no component registry was found.")
        return

    importer = queryMultiAdapter((sm, context), IBody, name=u"plone.app.workflow.sharing")
    if importer:
        body = context.readDataFile('sharing.xml')
        if body is not None:
            importer.body = body


def export_sharing(context):

    sm = getSiteManager(context.getSite())
    logger = context.getLogger('plone.app.workflow')

    if sm is None or not IComponentRegistry.providedBy(sm):
        logger.debug("Nothing to export.")
        return

    exporter = queryMultiAdapter((sm, context), IBody, name=u"plone.app.workflow.sharing")
    if exporter:
        body = exporter.body
        if body is not None:
            context.writeDataFile('sharing.xml', body, exporter.mime_type)
