import logging
import os
import os.path
from os.path import isdir

from zope.deprecation import deprecate

import Globals
from App.ImageFile import ImageFile
pts_globals = globals()

CACHE_PATH = os.path.join(Globals.INSTANCE_HOME, 'var', 'pts')
try:
    # Zope 2.13+
    from OFS.metaconfigure import get_registered_packages
    get_registered_packages  # pyflakes
except ImportError:
    def get_registered_packages():
        import Products
        return getattr(Products, '_registered_packages', ())

from AccessControl import ModuleSecurityInfo, allow_module
from AccessControl.Permissions import view
from OFS.Application import get_products

from Products.PlacelessTranslationService.load import (
    _load_i18n_dir, _remove_mo_cache)
from Products.PlacelessTranslationService.utils import log

# # Apply import time patches
if not bool(os.getenv('DISABLE_PTS')):
    import patches

# BBB
import warnings
showwarning = warnings.showwarning
warnings.showwarning = lambda *a, **k: None
# ignore deprecation warnings on import
from Products.PlacelessTranslationService.PlacelessTranslationService import (
    PlacelessTranslationService, PTSWrapper, PTS_IS_RTL)
# restore warning machinery
warnings.showwarning = showwarning

# id to use in the Control Panel
cp_id = 'TranslationService'

# module level translation service
translation_service = None

# icon
misc_ = {
    'PlacelessTranslationService.png':
    ImageFile('www/PlacelessTranslationService.png', globals()),
    'GettextMessageCatalog.png':
    ImageFile('www/GettextMessageCatalog.png', globals()),
    }

# set product-wide attrs for importing
security = ModuleSecurityInfo('Products.PlacelessTranslationService')
allow_module('Products.PlacelessTranslationService')

security.declarePrivate('os')
security.declarePrivate('logging')
security.declarePrivate('isdir')
security.declarePrivate('deprecate')
security.declarePrivate('Globals')
security.declarePrivate('ImageFile')
security.declarePrivate('pts_globals')
security.declarePrivate('CACHE_PATH')
security.declarePrivate('get_registered_packages')
security.declarePrivate('ModuleSecurityInfo')
security.declarePrivate('PTSWrapper')
security.declarePrivate('get_products')
security.declarePrivate('patches')
security.declarePrivate('warnings')
security.declarePrivate('misc_')
security.declarePrivate('os')


security.declareProtected(view, 'getTranslationService')
@deprecate("The getTranslationService method of PTS is deprecated and "
           "will be removed in the next major version of PTS.")
def getTranslationService():
    """returns the PTS instance
    """
    return translation_service

security.declarePrivate('make_translation_service')
@deprecate("The make_translation_service method of PTS is deprecated and "
           "will be removed in the next major version of PTS.")
def make_translation_service(cp):
    """Control_Panel translation service
    """
    global translation_service
    translation_service = PlacelessTranslationService('default')
    translation_service.id = cp_id
    cp._setObject(cp_id, translation_service)
    translation_service = PTSWrapper()
    return getattr(cp, cp_id)


IGNORED = frozenset([
    'BTreeFolder2', 'ExternalEditor', 'ExternalMethod', 'Five', 'MIMETools',
    'MailHost', 'OFSP', 'PageTemplates', 'PlacelessTranslationService',
    'PluginIndexes', 'PythonScripts', 'Sessions', 'SiteAccess', 'SiteErrorLog',
    'StandardCacheManagers', 'TemporaryFolder', 'Transience', 'ZCTextIndex',
    'ZCatalog', 'ZODBMountPoint', 'ZReST', 'ZSQLMethods',
])

security.declarePrivate('initialize2')
def initialize2(context):
    # allow for disabling PTS entirely by setting an environment variable.
    if bool(os.getenv('DISABLE_PTS')):
        log('Disabled by environment variable "DISABLE_PTS".', logging.WARNING)
        return

    cp = getattr(getattr(context, '_ProductContext__app', None), 'Control_Panel', None) # argh
    if cp is not None and cp_id in cp.objectIds():
        cp_ts = getattr(cp, cp_id, None)
        # Clean up ourselves
        if cp_ts is not None:
            cp._delObject(cp_id)
            _remove_mo_cache(CACHE_PATH)

    # load translation files from all packages and products
    loaded = {}

    import Products
    packages = get_registered_packages()
    for package in packages:
        name = package.__name__
        path = package.__path__[0]
        loaded[name] = True
        i18n_dir = os.path.join(path, 'i18n')
        if isdir(i18n_dir):
            _load_i18n_dir(i18n_dir)

    for product in get_products():
        name = product[1]
        if name in IGNORED:
            continue
        basepath = product[3]
        fullname = 'Products.' + name
        # Avoid loading products registered as packages twice
        if loaded.get(fullname):
            continue
        loaded[fullname] = True
        i18n_dir = os.path.join(basepath, name, 'i18n')
        if isdir(i18n_dir):
            _load_i18n_dir(i18n_dir)
