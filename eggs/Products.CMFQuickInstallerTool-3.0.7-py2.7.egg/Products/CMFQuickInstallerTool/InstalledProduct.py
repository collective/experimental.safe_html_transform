import logging
from zope.interface import implements
from zope.component import getSiteManager
from zope.component import queryUtility

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from DateTime import DateTime
from App.class_init import InitializeClass
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal
from Products.GenericSetup.utils import _resolveDottedName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFQuickInstallerTool.interfaces.portal_quickinstaller \
    import IInstalledProduct
from Products.CMFQuickInstallerTool.utils import get_method
from Products.CMFQuickInstallerTool.utils import get_install_method
from Products.CMFQuickInstallerTool.utils import updatelist, delObjects

logger = logging.getLogger('CMFQuickInstallerTool')

DEFAULT_CASCADE = (
    'types', 'skins', 'actions', 'portalobjects', 'workflows', 'slots',
    'registrypredicates', 'adapters', 'utilities',
)


class InstalledProduct(SimpleItem):
    """Class storing information about an installed product

      Let's make sure that this implementation actually fulfills the
      'IInstalledProduct' API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IInstalledProduct, InstalledProduct)
      True
    """
    implements(IInstalledProduct)

    meta_type = "Installed Product"

    manage_options = (
        {'label': 'View', 'action': 'manage_installationInfo'},
        ) + SimpleItem.manage_options

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'manage_installationInfo')
    manage_installationInfo = PageTemplateFile(
        'forms/installed_product_overview', globals(),
        __name__='manage_installationInfo')

    default_cascade = [
        'types', 'skins', 'actions', 'portalobjects', 'workflows', 'slots',
        'registrypredicates', 'adapters', 'utilities']

    def __init__(self, id):
        self.id = id
        self.transcript = []
        self.leftslots = []
        self.rightslots = []
        self.locked = None
        self.hidden = None
        self.installedversion = None
        self.status = 'new'
        self.error = False
        self.afterid = None
        self.beforeid = None
        for key in DEFAULT_CASCADE:
            setattr(self, key, [])

    security.declareProtected(ManagePortal, 'update')

    def update(self, settings, installedversion='', logmsg='',
               status='installed', error=False, locked=False, hidden=False,
               afterid=None, beforeid=None):

        # check for the availability of attributes before assigning
        for att in settings.keys():
            if not hasattr(self.aq_base, att):
                setattr(self, att, [])

        qi = getToolByName(self, 'portal_quickinstaller')
        reg = qi.getAlreadyRegistered()

        for k in settings.keys():
            old = k in reg.keys() and reg[k] or []
            updatelist(getattr(self, k), settings[k], old)

        self.transcript.insert(0, {'timestamp': DateTime(), 'msg': logmsg})
        self.locked = locked
        self.hidden = hidden
        self.installedversion = installedversion
        self.afterid = afterid
        self.beforeid = beforeid

        if status:
            self.status = status

        self.error = error

    security.declareProtected(ManagePortal, 'log')

    def log(self, logmsg):
        """Adds a log to the transcript
        """
        self.transcript.insert(0, {'timestamp': DateTime(), 'msg': logmsg})

    security.declareProtected(ManagePortal, 'hasError')

    def hasError(self):
        """Returns if the prod is in error state
        """
        return getattr(self, 'error', False)

    security.declareProtected(ManagePortal, 'isLocked')

    def isLocked(self):
        """Is the product locked for uninstall
        """
        return getattr(self, 'locked', False)

    security.declareProtected(ManagePortal, 'isHidden')

    def isHidden(self):
        """Is the product hidden
        """
        return getattr(self, 'hidden', False)

    security.declareProtected(ManagePortal, 'isVisible')

    def isVisible(self):
        return not self.isHidden()

    security.declareProtected(ManagePortal, 'isInstalled')

    def isInstalled(self):
        return self.status == 'installed'

    security.declareProtected(ManagePortal, 'getStatus')

    def getStatus(self):
        return self.status

    security.declareProtected(ManagePortal, 'getTypes')

    def getTypes(self):
        return self.types

    security.declareProtected(ManagePortal, 'getSkins')

    def getSkins(self):
        return self.skins

    security.declareProtected(ManagePortal, 'getActions')

    def getActions(self):
        return self.actions

    security.declareProtected(ManagePortal, 'getPortalObjects')

    def getPortalObjects(self):
        return self.portalobjects

    security.declareProtected(ManagePortal, 'getWorkflows')

    def getWorkflows(self):
        return self.workflows

    security.declareProtected(ManagePortal, 'getLeftSlots')

    def getLeftSlots(self):
        if getattr(self, 'leftslots', None) is None:
            self.leftslots = []
        return self.leftslots

    security.declareProtected(ManagePortal, 'getRightSlots')

    def getRightSlots(self):
        if getattr(self, 'rightslots', None) is None:
            self.rightslots = []
        return self.rightslots

    security.declareProtected(ManagePortal, 'getSlots')

    def getSlots(self):
        return self.getLeftSlots() + self.getRightSlots()

    security.declareProtected(ManagePortal, 'getValue')

    def getValue(self, name):
        return getattr(self, name, [])

    security.declareProtected(ManagePortal, 'getRegistryPredicates')

    def getRegistryPredicates(self):
        """Return the custom entries in the content_type_registry
        """
        return getattr(self, 'registrypredicates', [])

    security.declareProtected(ManagePortal, 'getAfterId')

    def getAfterId(self):
        return self.afterid

    security.declareProtected(ManagePortal, 'getBeforeId')

    def getBeforeId(self):
        return self.beforeid

    security.declareProtected(ManagePortal, 'getTranscriptAsText')

    def getTranscriptAsText(self):
        if getattr(self, 'transcript', None):
            msgs = [t['timestamp'].ISO() + '\n' + str(t['msg'])
                    for t in self.transcript]
            return '\n=============\n'.join(msgs)
        else:
            return 'no messages'

    def _getMethod(self, modfunc):
        """Returns a method
        """
        return get_method(self.id, modfunc)

    security.declareProtected(ManagePortal, 'getInstallMethod')

    def getInstallMethod(self):
        """ returns the installer method """
        res = get_install_method(self.id)
        if res is None:
            raise AttributeError('No Install method found for '
                                 'product %s' % self.id)
        else:
            return res

    security.declareProtected(ManagePortal, 'getUninstallMethod')

    def getUninstallMethod(self):
        """ returns the uninstaller method """
        return self._getMethod((('Install', 'uninstall'),
                                ('Install', 'Uninstall'),
                                ('install', 'uninstall'),
                                ('install', 'Uninstall'),
                               ))

    security.declareProtected(ManagePortal, 'getAfterInstallMethod')

    def getAfterInstallMethod(self):
        """ returns the after installer method """
        return self._getMethod((('Install', 'afterInstall'),
                                ('install', 'afterInstall'),
                               ))

    security.declareProtected(ManagePortal, 'getBeforeUninstallMethod')

    def getBeforeUninstallMethod(self):
        """ returns the before uninstaller method """
        return self._getMethod((('Install', 'beforeUninstall'),
                                ('install', 'beforeUninstall'),
                               ))

    security.declareProtected(ManagePortal, 'uninstall')

    def uninstall(self, cascade=default_cascade, reinstall=False, REQUEST=None):
        """Uninstalls the product and removes its dependencies
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()

        # TODO eventually we will land Event system and could remove
        # this 'removal_inprogress' hack
        if self.isLocked() and getattr(portal, 'removal_inprogress', False):
            raise ValueError('The product is locked and cannot be uninstalled!')

        res = ''
        afterRes = ''

        uninstaller = self.getUninstallMethod()
        beforeUninstall = self.getBeforeUninstallMethod()

        if uninstaller:
            uninstaller = uninstaller.__of__(portal)
            try:
                res = uninstaller(portal, reinstall=reinstall)
                # XXX log it
            except TypeError:
                res = uninstaller(portal)

        if beforeUninstall:
            beforeUninstall = beforeUninstall.__of__(portal)
            beforeRes, cascade = beforeUninstall(portal, reinstall=reinstall,
                                                product=self, cascade=cascade)

        self._cascadeRemove(cascade)

        self.status = 'uninstalled'
        self.log('uninstalled\n' + str(res) + str(afterRes))

        if REQUEST and REQUEST.get('nextUrl', None):
            return REQUEST.RESPONSE.redirect(REQUEST['nextUrl'])

    def _cascadeRemove(self, cascade):
        """Cascaded removal of objects
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()

        if 'types' in cascade:
            portal_types = getToolByName(self, 'portal_types')
            delObjects(portal_types, getattr(aq_base(self), 'types', []))

        if 'skins' in cascade:
            portal_skins = getToolByName(self, 'portal_skins')
            delObjects(portal_skins, getattr(aq_base(self), 'skins', []))

        if 'actions' in cascade and len(getattr(aq_base(self), 'actions', [])) > 0:
            portal_actions = getToolByName(self, 'portal_actions')
            for info in self.actions:
                if isinstance(info, basestring):
                    action = info
                    # Product was installed before CMF 2.1
                    # Try to remove the action from all categories
                    for category in portal_actions.objectIds():
                        cat = portal_actions[category]
                        if action in cat.objectIds():
                            cat._delObject(action)
                else:
                    category, action = info
                    if category in portal_actions.objectIds():
                        cat = portal_actions[category]
                        if action in cat.objectIds():
                            cat._delObject(action)
                        if len(cat.objectIds()) == 0:
                            del cat
                            portal_actions._delObject(category)

        if 'portalobjects' in cascade:
            delObjects(portal, getattr(aq_base(self), 'portalobjects', []))

        if 'workflows' in cascade:
            portal_workflow = getToolByName(self, 'portal_workflow')
            delObjects(portal_workflow, getattr(aq_base(self), 'workflows', []))

        if 'slots' in cascade:
            if self.getLeftSlots():
                portal.left_slots = [s for s in portal.left_slots
                                   if s not in self.getLeftSlots()]
            if self.getRightSlots():
                portal.right_slots = [s for s in portal.right_slots
                                    if s not in self.getRightSlots()]

        if 'registrypredicates' in cascade:
            ctr = getToolByName(self, 'content_type_registry')
            ids = [id for id, predicate in ctr.listPredicates()]
            predicates = getattr(aq_base(self), 'registrypredicates', [])
            for p in predicates:
                if p in ids:
                    ctr.removePredicate(p)
                else:
                    logger.warning("Failed to delete '%s' from content type "
                                   "registry" % p)

        if 'adapters' in cascade:
            adapters = getattr(aq_base(self), 'adapters', [])
            if adapters:
                sm = getSiteManager()
                # TODO: expand this to actually cover adapter registrations

        if 'utilities' in cascade:
            utilities = getattr(aq_base(self), 'utilities', [])
            if utilities:
                sm = getSiteManager()
                mapping = sm.objectItems()

                for registration in utilities:
                    provided = _resolveDottedName(registration[0])
                    name = registration[1]
                    utility = queryUtility(provided, name=name)

                    if utility is not None:
                        sm.unregisterUtility(provided=provided, name=name)

                        # Make sure utilities are removed from the
                        # site manager's mapping as well
                        for name, value in mapping:
                            if value is utility:
                                sm._delObject(name, suppress_events=True)

        rr_js = getToolByName(self, 'portal_javascripts', None)
        rr_css = getToolByName(self, 'portal_css', None)

        if rr_js is not None:
            for js in getattr(aq_base(self), 'resources_js', []):
                rr_js.unregisterResource(js)
        if rr_css is not None:
            for css in getattr(aq_base(self), 'resources_css', []):
                rr_css.unregisterResource(css)

        portal_controlpanel = getToolByName(self, 'portal_controlpanel', None)
        if portal_controlpanel is not None:
            portal_controlpanel.unregisterApplication(self.id)

    security.declareProtected(ManagePortal, 'getInstalledVersion')

    def getInstalledVersion(self):
        """Return the version of the product in the moment of installation
        """
        return getattr(self, 'installedversion', None)

InitializeClass(InstalledProduct)
