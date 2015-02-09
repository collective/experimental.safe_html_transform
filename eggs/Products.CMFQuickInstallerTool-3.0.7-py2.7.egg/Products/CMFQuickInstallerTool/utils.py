import logging
import os
import os.path

from Acquisition import aq_base
from OFS.Application import get_products
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from zExceptions import BadRequest
from zExceptions import NotFound
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IFolderish

from OFS.metaconfigure import get_registered_packages

logger = logging.getLogger('CMFQuickInstallerTool')

IGNORED = frozenset([
    'BTreeFolder2', 'ExternalEditor', 'ExternalMethod', 'Five', 'MIMETools',
    'MailHost', 'OFSP', 'PageTemplates', 'PluginIndexes', 'PythonScripts',
    'Sessions', 'SiteAccess', 'SiteErrorLog', 'StandardCacheManagers',
    'TemporaryFolder', 'Transience', 'ZCTextIndex', 'ZCatalog',
    'ZODBMountPoint', 'ZReST', 'ZSQLMethods',
])


def updatelist(a, b, c=None):
    for l in b:
        if l not in a:
            if c is None:
                a.append(l)
            else:
                if l not in c:
                    a.append(l)


def delObjects(cont, ids):
    """ abbreviation to delete objects """
    delids = [id for id in ids if hasattr(aq_base(cont), id)]
    for delid in delids:
        try:
            obj = cont.get(delid)
            if not (IContentish.providedBy(obj) or IFolderish.providedBy(obj)):
                cont.manage_delObjects(delid)
        except (AttributeError, KeyError, BadRequest):
            logger.warning("Failed to delete '%s' in '%s'" % (delid, cont.id))


def get_packages():
    """Returns a dict of package name to package path."""
    result = {}

    packages = get_registered_packages()
    for package in packages:
        name = package.__name__
        path = package.__path__[0]
        result[name] = path

    for product in get_products():
        name = product[1]
        if name in IGNORED:
            continue
        basepath = product[3]
        fullname = 'Products.' + name
        # Avoid getting products registered as packages twice
        if result.get(fullname):
            continue
        result[fullname] = os.path.join(basepath, name)

    return result


def get_install_method(productname):
    modfunc = (('Install', 'install'),
               ('Install', 'Install'),
               ('install', 'install'),
               ('install', 'Install'))
    return get_method(productname, modfunc)


def get_method(productname, modfunc):
    packages = get_packages()
    package = packages.get(productname, None)
    if package is None:
        package = packages.get('Products.' + productname, None)
        if package is None:
            return None

    extensions = os.path.join(package, 'Extensions')
    if not os.path.isdir(extensions):
        return None

    files = os.listdir(extensions)
    for mod, func in modfunc:
        if mod + '.py' in files:
            try:
                # id, title, module, function
                return ExternalMethod('temp', 'temp',
                                      productname + '.' + mod, func)
            except (NotFound, ImportError, RuntimeError):
                pass

    return None
