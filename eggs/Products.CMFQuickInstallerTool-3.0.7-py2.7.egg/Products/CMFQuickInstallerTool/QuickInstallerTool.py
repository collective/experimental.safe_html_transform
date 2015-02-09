import logging
import os

import pkg_resources

from zope.component import getSiteManager
from zope.component import getAllUtilitiesRegisteredFor
from zope.interface import implements
from zope.annotation.interfaces import IAnnotatable
from zope.i18nmessageid import MessageFactory

from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Acquisition import aq_base, aq_parent, aq_get, aq_inner

from Globals import DevelopmentMode
from App.class_init import InitializeClass
from Globals import INSTANCE_HOME
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager

from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.GenericSetup import EXTENSION
from Products.GenericSetup.utils import _getDottedName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFQuickInstallerTool.interfaces import INonInstallable
from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool
from Products.CMFQuickInstallerTool.InstalledProduct import InstalledProduct
from Products.CMFQuickInstallerTool.utils import get_install_method
from Products.CMFQuickInstallerTool.utils import get_packages
_ = MessageFactory("plone")

try:
    # Allow IPloneSiteRoot or ISiteRoot if we have Plone
    from Products.CMFPlone.interfaces import IPloneSiteRoot as ISiteRoot
    ISiteRoot   # pyflakes
except ImportError:
    from Products.CMFCore.interfaces import ISiteRoot

logger = logging.getLogger('CMFQuickInstallerTool')


class AlreadyInstalled(Exception):
    """ Would be nice to say what Product was trying to be installed """
    pass


def addQuickInstallerTool(self, REQUEST=None):
    """ """
    qt = QuickInstallerTool()
    self._setObject('portal_quickinstaller', qt, set_owner=False)
    if REQUEST:
        return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


class HiddenProducts(object):
    implements(INonInstallable)

    def getNonInstallableProducts(self):
        return ['CMFQuickInstallerTool', 'Products.CMFQuickInstallerTool']


class QuickInstallerTool(UniqueObject, ObjectManager, SimpleItem):
    """
      Let's make sure that this implementation actually fulfills the
      'IQuickInstallerTool' API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IQuickInstallerTool, QuickInstallerTool)
      True
    """
    implements(IQuickInstallerTool)

    meta_type = 'CMF QuickInstaller Tool'
    id = 'portal_quickinstaller'

    security = ClassSecurityInfo()

    manage_options = (
        {'label': 'Install', 'action': 'manage_installProductsForm'},
        ) + ObjectManager.manage_options

    security.declareProtected(ManagePortal, 'manage_installProductsForm')
    manage_installProductsForm = PageTemplateFile(
        'forms/install_products_form', globals(),
        __name__='manage_installProductsForm')

    security = ClassSecurityInfo()

    def __init__(self):
        self.id = 'portal_quickinstaller'

    @property
    def errors(self):
        return getattr(self, '_v_errors', {})

    security.declareProtected(ManagePortal, 'getInstallProfiles')

    def getInstallProfiles(self, productname):
        """ Return the installer profile id
        """
        portal_setup = getToolByName(self, 'portal_setup')
        profiles = portal_setup.listProfileInfo()

        # We are only interested in extension profiles for the product
        # TODO Remove the manual Products.* check here. It is still needed.
        profiles = [prof['id'] for prof in profiles if
            prof['type'] == EXTENSION and
            (prof['product'] == productname or
             prof['product'] == 'Products.%s' % productname)]

        return profiles

    security.declareProtected(ManagePortal, 'getInstallProfile')

    def getInstallProfile(self, productname):
        """ Return the installer profile
        """
        portal_setup = getToolByName(self, 'portal_setup')
        profiles = portal_setup.listProfileInfo()

        # We are only interested in extension profiles for the product
        profiles = [prof for prof in profiles if
            prof['type'] == EXTENSION and
            (prof['product'] == productname or
             prof['product'] == 'Products.%s' % productname)]

        # XXX Currently QI always uses the first profile
        if profiles:
            return profiles[0]
        return None

    security.declareProtected(ManagePortal, 'getInstallMethod')

    def getInstallMethod(self, productname):
        """ Return the installer method
        """
        res = get_install_method(productname)
        if res is None:
            raise AttributeError('No Install method found for '
                                 'product %s' % productname)
        return res

    security.declareProtected(ManagePortal, 'getBrokenInstalls')

    def getBrokenInstalls(self):
        """ Return all the broken installs """
        errs = getattr(self, "_v_errors", {})
        return errs.values()

    security.declareProtected(ManagePortal, 'isProductInstallable')

    def isProductInstallable(self, productname):
        """Asks wether a product is installable by trying to get its install
           method or an installation profile.
        """
        not_installable = []
        utils = getAllUtilitiesRegisteredFor(INonInstallable)
        for util in utils:
            not_installable.extend(util.getNonInstallableProducts())
        if productname in not_installable:
            return False
        try:
            self.getInstallMethod(productname)
            return True
        except AttributeError:
            profiles = self.getInstallProfiles(productname)
            if not profiles:
                return False
            setup_tool = getToolByName(self, 'portal_setup')
            try:
                # XXX Currently QI always uses the first profile
                setup_tool.getProfileDependencyChain(profiles[0])
            except KeyError, e:
                if not getattr(self, "_v_errors", {}):
                    self._v_errors = {}
                # Don't show twice the same error: old install and profile
                # oldinstall is test in first in other methods we may have an
                # extra 'Products.' in the namespace
                checkname = productname
                if checkname.startswith('Products.'):
                    checkname = checkname[9:]
                else:
                    checkname = 'Products.' + checkname
                if checkname in self._v_errors:
                    if self._v_errors[checkname]['value'] == e.args[0]:
                        return False
                    else:
                        # A new error is found, register it
                        self._v_errors[productname] = dict(
                            type=_(u"dependency_missing", default=u"Missing dependency"),
                            value=e.args[0],
                            productname=productname)
                else:
                    self._v_errors[productname] = dict(
                        type=_(u"dependency_missing", default=u"Missing dependency"),
                        value=e.args[0],
                        productname=productname)

                return False

            return True

    security.declareProtected(ManagePortal, 'isProductAvailable')
    isProductAvailable = isProductInstallable

    security.declareProtected(ManagePortal, 'listInstallableProfiles')

    def listInstallableProfiles(self):
        """List candidate products which have a GS profiles.
        """
        portal_setup = getToolByName(self, 'portal_setup')
        profiles = portal_setup.listProfileInfo(ISiteRoot)

        # We are only interested in extension profiles
        profiles = [prof['product'] for prof in profiles if
            prof['type'] == EXTENSION]
        return set(profiles)

    security.declareProtected(ManagePortal, 'listInstallableProducts')

    def listInstallableProducts(self, skipInstalled=True):
        """List candidate CMF products for installation -> list of dicts
           with keys:(id,title,hasError,status)
        """
        # reset the list of broken products
        if getattr(self, '_v_errors', True):
            self._v_errors = {}

        # Returns full names with Products. prefix for all packages / products
        packages = get_packages()

        pids = []
        for p in packages:
            if not self.isProductInstallable(p):
                continue
            if p.startswith('Products.'):
                p = p[9:]
            pids.append(p)

        # Get product list from the extension profiles
        profile_pids = self.listInstallableProfiles()

        for p in profile_pids:
            if p in pids or p in packages:
                continue
            if not self.isProductInstallable(p):
                continue
            pids.append(p)

        if skipInstalled:
            installed = [p['id'] for p in self.listInstalledProducts(showHidden=True)]
            pids = [r for r in pids if r not in installed]

        res = []
        for r in pids:
            p = self._getOb(r, None)
            name = r
            profile = self.getInstallProfile(r)
            if profile:
                name = profile['title']
            if p:
                res.append({'id': r, 'title': name, 'status': p.getStatus(),
                            'hasError': p.hasError()})
            else:
                res.append({'id': r, 'title': name, 'status': 'new', 'hasError': False})
        res.sort(lambda x, y: cmp(x.get('title', x.get('id', None)),
                                 y.get('title', y.get('id', None))))
        return res

    security.declareProtected(ManagePortal, 'listInstalledProducts')

    def listInstalledProducts(self, showHidden=False):
        """Returns a list of products that are installed -> list of
        dicts with keys:(id, title, hasError, status, isLocked, isHidden,
        installedVersion)
        """
        pids = [o.id for o in self.objectValues()
                if o.isInstalled() and (o.isVisible() or showHidden)]
        pids = [pid for pid in pids if self.isProductInstallable(pid)]

        res = []

        for r in pids:
            p = self._getOb(r, None)
            name = r
            profile = self.getInstallProfile(r)
            if profile:
                name = profile['title']

            res.append({'id': r,
                        'title': name,
                        'status': p.getStatus(),
                        'hasError': p.hasError(),
                        'isLocked': p.isLocked(),
                        'isHidden': p.isHidden(),
                        'installedVersion': p.getInstalledVersion()})
        res.sort(lambda x, y: cmp(x.get('title', x.get('id', None)),
                                  y.get('title', y.get('id', None))))
        return res

    security.declareProtected(ManagePortal, 'getProductFile')

    def getProductFile(self, p, fname='readme.txt'):
        """Return the content of a file of the product
        case-insensitive, if it does not exist -> None
        """
        packages = get_packages()
        prodpath = packages.get(p)
        if prodpath is None:
            prodpath = packages.get('Products.' + p)

        if prodpath is None:
            return None

        # now list the directory to get the readme.txt case-insensitive
        try:
            files = os.listdir(prodpath)
        except OSError:
            return None

        for f in files:
            if f.lower() == fname:
                text = open(os.path.join(prodpath, f)).read()
                try:
                    return unicode(text)
                except UnicodeDecodeError:
                    try:
                        return unicode(text, 'utf-8')
                    except UnicodeDecodeError:
                        return unicode(text, 'utf-8', 'replace')
        return None

    security.declareProtected(ManagePortal, 'getProductReadme')
    getProductReadme = getProductFile

    security.declareProtected(ManagePortal, 'getProductDescription')

    def getProductDescription(self, p):
        """Returns the profile description for a given product.
        """
        profile = self.getInstallProfile(p)
        if profile is None:
            return None
        return profile.get('description', None)

    security.declareProtected(ManagePortal, 'getProductVersion')

    def getProductVersion(self, p):
        """Return the version string stored in version.txt.
        """
        try:
            dist = pkg_resources.get_distribution(p)
            return dist.version
        except pkg_resources.DistributionNotFound:
            pass

        if "." not in p:
            try:
                dist = pkg_resources.get_distribution("Products." + p)
                return dist.version
            except pkg_resources.DistributionNotFound:
                pass

        res = self.getProductFile(p, 'version.txt')
        if res is not None:
            res = res.strip()
        return res

    security.declareProtected(ManagePortal, 'snapshotPortal')

    def snapshotPortal(self, portal):
        portal_types = getToolByName(portal, 'portal_types')
        portal_skins = getToolByName(portal, 'portal_skins')
        portal_actions = getToolByName(portal, 'portal_actions')
        portal_workflow = getToolByName(portal, 'portal_workflow')
        type_registry = getToolByName(portal, 'content_type_registry')

        state = {}
        state['leftslots'] = getattr(portal, 'left_slots', [])
        if callable(state['leftslots']):
            state['leftslots'] = state['leftslots']()
        state['rightslots'] = getattr(portal, 'right_slots', [])
        if callable(state['rightslots']):
            state['rightslots'] = state['rightslots']()
        state['registrypredicates'] = [pred[0] for pred in type_registry.listPredicates()]

        state['types'] = portal_types.objectIds()
        state['skins'] = portal_skins.objectIds()
        actions = set()
        for category in portal_actions.objectIds():
            for action in portal_actions[category].objectIds():
                actions.add((category, action))
        state['actions'] = actions
        state['workflows'] = portal_workflow.objectIds()
        state['portalobjects'] = portal.objectIds()
        state['adapters'] = tuple(getSiteManager().registeredAdapters())
        state['utilities'] = tuple(getSiteManager().registeredUtilities())

        jstool = getToolByName(portal, 'portal_javascripts', None)
        state['resources_js'] = jstool and jstool.getResourceIds() or []
        csstool = getToolByName(portal, 'portal_css', None)
        state['resources_css'] = csstool and csstool.getResourceIds() or []
        return state

    security.declareProtected(ManagePortal, 'deriveSettingsFromSnapshots')

    def deriveSettingsFromSnapshots(self, before, after):
        actions = [a for a in (after['actions'] - before['actions'])]

        adapters = []
        if len(after['adapters']) > len(before['adapters']):
            registrations = [reg for reg in after['adapters']
                             if reg not in before['adapters']]
            # TODO: expand this to actually cover adapter registrations

        utilities = []
        if len(after['utilities']) > len(before['utilities']):
            registrations = [reg for reg in after['utilities']
                             if reg not in before['utilities']]

            for registration in registrations:
                reg = (_getDottedName(registration.provided), registration.name)
                utilities.append(reg)

        settings = dict(
            types=[t for t in after['types'] if t not in before['types']],
            skins=[s for s in after['skins'] if s not in before['skins']],
            actions=actions,
            workflows=[w for w in after['workflows'] if w not in before['workflows']],
            portalobjects=[a for a in after['portalobjects']
                           if a not in before['portalobjects']],
            leftslots=[s for s in after['leftslots'] if s not in before['leftslots']],
            rightslots=[s for s in after['rightslots'] if s not in before['rightslots']],
            adapters=adapters,
            utilities=utilities,
            registrypredicates=[s for s in after['registrypredicates']
                                if s not in before['registrypredicates']],
            )

        jstool = getToolByName(self, 'portal_javascripts', None)
        if jstool is not None:
            settings['resources_js'] = [r for r in after['resources_js'] if r not in before['resources_js']]
            settings['resources_css'] = [r for r in after['resources_css'] if r not in before['resources_css']]

        return settings

    security.declareProtected(ManagePortal, 'installProduct')

    def installProduct(self, p, locked=False, hidden=False,
                       swallowExceptions=None, reinstall=False,
                       forceProfile=False, omitSnapshots=True,
                       profile=None, blacklistedSteps=None):
        """Install a product by name
        """
        __traceback_info__ = (p, )

        if profile is not None:
            forceProfile = True

        if self.isProductInstalled(p):
            prod = self._getOb(p)
            msg = ('This product is already installed, '
                   'please uninstall before reinstalling it.')
            prod.log(msg)
            return msg

        portal = aq_parent(aq_inner(self))

        before = self.snapshotPortal(portal)

        if hasattr(self, "REQUEST"):
            reqstorage = IAnnotatable(self.REQUEST, None)
            if reqstorage is not None:
                installing = reqstorage.get("Products.CMFQUickInstaller.Installing", set())
                installing.add(p)
        else:
            reqstorage = None

        # XXX We can not use getToolByName since that returns a utility
        # without a RequestContainer. This breaks import steps that need
        # to run tools which request self.REQUEST.
        portal_setup = aq_get(portal, 'portal_setup', None, 1)
        status = None
        res = ''

        # Create a snapshot before installation
        before_id = portal_setup._mangleTimestampName('qi-before-%s' % p)
        if not omitSnapshots:
            portal_setup.createSnapshot(before_id)

        install = False
        if not forceProfile:
            try:
                # Install via external method
                install = self.getInstallMethod(p).__of__(portal)
            except AttributeError:
                # No classic install method found
                pass

        if install and not forceProfile:
            try:
                res = install(portal, reinstall=reinstall)
            except TypeError:
                res = install(portal)
            status = 'installed'
        else:
            profiles = self.getInstallProfiles(p)
            if profiles:
                if profile is None:
                    profile = profiles[0]
                    if len(profiles) > 1:
                        logger.log(logging.INFO,
                                   'Multiple extension profiles found for product '
                                   '%s. Used profile: %s' % (p, profile))

                portal_setup.runAllImportStepsFromProfile(
                    'profile-%s' % profile,
                    blacklisted_steps=blacklistedSteps,
                )
                status = 'installed'
            else:
                # No install method and no profile, log / abort?
                pass

        if reqstorage is not None:
            installing.remove(p)

        # Create a snapshot after installation
        after_id = portal_setup._mangleTimestampName('qi-after-%s' % p)
        if not omitSnapshots:
            portal_setup.createSnapshot(after_id)

        if profile:
            # If installation was done via a profile, the settings were already
            # snapshotted in the IProfileImportedEvent handler, and we should
            # use those because the ones derived here include settings from
            # dependency profiles.
            settings = {}
        else:
            after = self.snapshotPortal(portal)
            settings = self.deriveSettingsFromSnapshots(before, after)

        rr_css = getToolByName(self, 'portal_css', None)
        if rr_css is not None:
            if 'resources_css' in settings and len(settings['resources_css']) > 0:
                rr_css.cookResources()

        msg = str(res)
        version = self.getProductVersion(p)

        # add the product
        self.notifyInstalled(
            p,
            settings=settings,
            installedversion=version,
            logmsg=res,
            status=status,
            error=False,
            locked=locked,
            hidden=hidden,
            afterid=after_id,
            beforeid=before_id)

        prod = getattr(self, p)
        afterInstall = prod.getAfterInstallMethod()
        if afterInstall is not None:
            afterInstall = afterInstall.__of__(portal)
            afterRes = afterInstall(portal, reinstall=reinstall, product=prod)
            if afterRes:
                res = res + '\n' + str(afterRes)
        return res

    security.declareProtected(ManagePortal, 'installProducts')

    def installProducts(self, products=None, stoponerror=True, reinstall=False,
                        REQUEST=None, forceProfile=False, omitSnapshots=True):
        """ """
        if products is None:
            products = []
        res = """
    Installed Products
    ====================
    """
        # return products
        for p in products:
            res += p + ':'
            r = self.installProduct(p, swallowExceptions=not stoponerror,
                                  reinstall=reinstall,
                                  forceProfile=forceProfile,
                                  omitSnapshots=omitSnapshots)
            res += 'ok:\n'
            if r:
                res += str(r) + '\n'
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

        return res

    security.declareProtected(ManagePortal, 'isProductInstalled')

    def isProductInstalled(self, productname):
        """Check wether a product is installed (by name)
        """
        o = self._getOb(productname, None)
        return o is not None and o.isInstalled()

    security.declareProtected(ManagePortal, 'notifyInstalled')

    def notifyInstalled(self, p, locked=True, hidden=False, settings={}, **kw):
        """Marks a product that has been installed
        without QuickInstaller as installed
        """

        if p not in self.objectIds():
            ip = InstalledProduct(p)
            self._setObject(p, ip)

        p = getattr(self, p)
        p.update(settings, locked=locked, hidden=hidden, **kw)

    security.declareProtected(ManagePortal, 'uninstallProducts')

    def uninstallProducts(self, products=None,
                          cascade=InstalledProduct.default_cascade,
                          reinstall=False,
                          REQUEST=None):
        """Removes a list of products
        """
        if products is None:
            products = []
        for pid in products:
            prod = getattr(self, pid)
            prod.uninstall(cascade=cascade, reinstall=reinstall)
            if not reinstall:
                self.manage_delObjects(pid)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])
    uninstallProducts = postonly(uninstallProducts)

    security.declareProtected(ManagePortal, 'reinstallProducts')

    def reinstallProducts(self, products, REQUEST=None, omitSnapshots=True):
        """Reinstalls a list of products, the main difference to
        uninstall/install is that it does not remove portal objects
        created during install (e.g. tools, etc.)
        """
        if isinstance(products, basestring):
            products = [products]

        # only delete everything EXCEPT portalobjects (tools etc) for reinstall
        cascade = [c for c in InstalledProduct.default_cascade
                 if c != 'portalobjects']
        self.uninstallProducts(products, cascade, reinstall=True)
        self.installProducts(products,
                             stoponerror=True,
                             reinstall=True,
                             omitSnapshots=omitSnapshots)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    reinstallProducts = postonly(reinstallProducts)

    def getQIElements(self):
        res = ['types', 'skins', 'actions', 'portalobjects', 'workflows',
                  'leftslots', 'rightslots', 'registrypredicates',
                  'resources_js', 'resources_css']
        return res

    def getAlreadyRegistered(self):
        """Get a list of already registered elements
        """
        result = {}
        products = [p for p in self.objectValues() if p.isInstalled()]
        for element in self.getQIElements():
            v = result.setdefault(element, [])
            for product in products:
                pv = getattr(aq_base(product), element, None)
                if pv:
                    v.extend(list(pv))
        return result

    security.declareProtected(ManagePortal, 'isDevelopmentMode')

    def isDevelopmentMode(self):
        """Is the Zope server in debug mode?
        """
        return not not DevelopmentMode

    security.declareProtected(ManagePortal, 'getInstanceHome')

    def getInstanceHome(self):
        """Return location of $INSTANCE_HOME
        """
        return INSTANCE_HOME

InitializeClass(QuickInstallerTool)
