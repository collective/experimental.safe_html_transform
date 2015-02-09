from zope.component import adapter
from zope.component import getAllUtilitiesRegisteredFor
from zope.annotation.interfaces import IAnnotatable

from Acquisition import aq_parent

from Products.GenericSetup.interfaces import IBeforeProfileImportEvent
from Products.GenericSetup.interfaces import IProfileImportedEvent
from Products.CMFCore.utils import getToolByName

FILTER_PROFILES = True
try:
    from Products.CMFPlone.interfaces import INonInstallable
except ImportError:
    FILTER_PROFILES = False


class SorryNoCaching(object):
    pass


def findProductForProfile(context, profile_id, qi):
    # Cache installable products list to cut portal creation time
    request = getattr(context, 'REQUEST', SorryNoCaching())
    if not getattr(request, '_cachedInstallableProducts', ()):
        request._cachedInstallableProducts = qi.listInstallableProducts(skipInstalled=False)

    for product in request._cachedInstallableProducts:
        profiles = qi.getInstallProfiles(product["id"])
        if profile_id in profiles:
            return product["id"]

    return None


@adapter(IBeforeProfileImportEvent)
def handleBeforeProfileImportEvent(event):
    profile_id = event.profile_id
    if profile_id is None or not event.full_import:
        return

    if profile_id.startswith("profile-"):
        profile_id = profile_id[8:]
    context = event.tool

    # We need a request to scribble some data in
    request = getattr(context, "REQUEST", None)
    if request is None:
        return

    if FILTER_PROFILES:
        ignore_profiles = getattr(request, '_cachedIgnoredProfiles', ())
        if not ignore_profiles:
            ignore_profiles = []
            utils = getAllUtilitiesRegisteredFor(INonInstallable)
            for util in utils:
                ignore_profiles.extend(util.getNonInstallableProfiles())
            request._cachedIgnoredProfiles = tuple(ignore_profiles)

        if profile_id in ignore_profiles:
            return

    qi = getToolByName(context, "portal_quickinstaller", None)
    if qi is None:
        return

    product = findProductForProfile(context, profile_id, qi)
    if product is None:
        return

    snapshot = qi.snapshotPortal(aq_parent(context))

    storage = IAnnotatable(request, None)
    if storage is None:
        return

    installing = storage.get("Products.CMFQuickInstaller.Installing", [])
    if product in installing:
        return

    if storage.has_key("Products.CMFQuickInstallerTool.Events"):
        data = storage["Products.CMFQuickInstallerTool.Events"]
    else:
        data = storage["Products.CMFQuickInstallerTool.Events"] = {}
    data[event.profile_id] = dict(product=product, snapshot=snapshot)


@adapter(IProfileImportedEvent)
def handleProfileImportedEvent(event):
    if event.profile_id is None or not event.full_import:
        return

    context = event.tool

    # We need a request to scribble some data in
    request = getattr(context, "REQUEST", None)
    if request is None:
        return

    storage = IAnnotatable(request, None)
    if storage is None:
        return

    data = storage.get("Products.CMFQuickInstallerTool.Events", [])
    if event.profile_id not in data:
        return
    info = data[event.profile_id]

    qi = getToolByName(context, "portal_quickinstaller", None)
    if qi is None:
        return

    after = qi.snapshotPortal(aq_parent(context))

    settings = qi.deriveSettingsFromSnapshots(info["snapshot"], after)
    version = qi.getProductVersion(info["product"])
    qi.notifyInstalled(
            info["product"],
            locked=False,
            logmsg="Installed via setup tool",
            settings=settings,
            installedversion=version,
            status='installed',
            error=False)
