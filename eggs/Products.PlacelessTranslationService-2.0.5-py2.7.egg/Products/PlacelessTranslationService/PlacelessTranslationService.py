import sys, os, re
import logging

from os.path import join

import zope.deprecation
from zope.component import queryUtility
from zope.i18n import interpolate as z3interpolate
from zope.i18n import translate as z3translate
from zope.i18n import _interp_regex
from zope.i18n import NAME_RE
from zope.interface import implements
from zope.publisher.interfaces.browser import IBrowserRequest

import Globals
from ExtensionClass import Base
from Acquisition import aq_acquire
from Acquisition import ImplicitAcquisitionWrapper
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, view_management_screens
from App.class_init import InitializeClass
from OFS.Folder import Folder

from Products.PlacelessTranslationService.GettextMessageCatalog import (
    BrokenMessageCatalog, GettextMessageCatalog,
    translationRegistry, rtlRegistry)
from Products.PlacelessTranslationService.Negotiator import negotiator
from Products.PlacelessTranslationService.Domain import Domain
from Products.PlacelessTranslationService.interfaces import \
    IPlacelessTranslationService
from Products.PlacelessTranslationService.load import (_checkLanguage,
    _load_i18n_dir, _updateMoFile, _register_catalog_file)
from Products.PlacelessTranslationService.memoize import memoize
from Products.PlacelessTranslationService.utils import log, Registry

PTS_IS_RTL = '_pts_is_rtl'

_marker = []

# Setting up regular expression for finding interpolation variables in the text.
_get_var_regex = re.compile(r'%(n)s' %({'n': NAME_RE}))

# Note that these fallbacks are used only to find a catalog.  If a particular
# message in a catalog is not translated, tough luck, you get the msgid.
LANGUAGE_FALLBACKS = list(os.environ.get('LANGUAGE_FALLBACKS', 'en').split(' '))

catalogRegistry = Registry()
registerCatalog = catalogRegistry.register
fbcatalogRegistry = Registry()
registerFBCatalog = fbcatalogRegistry.register

class PTSWrapper(Base):
    """
    Wrap the persistent PTS since persistent
    objects can't be passed around threads.
    """
    security = ClassSecurityInfo()

    security.declareProtected(view, 'translate')
    def translate(self, domain, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        # Translate a message using Unicode.
        return z3translate(msgid, domain, mapping, context,
                           target_language, default)

    security.declarePublic(view, 'getLanguageName')
    def getLanguageName(self, code, context):
        service = queryUtility(IPlacelessTranslationService)
        if service is not None:
            return service.getLanguageName(code)
        return None

    security.declarePublic(view, 'getLanguages')
    def getLanguages(self, context, domain=None):
        service = queryUtility(IPlacelessTranslationService)
        if service is not None:
            return service.getLanguages(domain)
        return None

    security.declarePrivate('negotiate_language')
    def negotiate_language(self, context, domain):
        service = queryUtility(IPlacelessTranslationService)
        if service is not None:
            return service.negotiate_language(context.REQUEST,domain)
        return None

InitializeClass(PTSWrapper)


class PlacelessTranslationService(Folder):
    """
    The Placeless Translation Service
    """
    implements(IPlacelessTranslationService)

    meta_type = title = 'Placeless Translation Service'
    icon = 'misc_/PlacelessTranslationService/PlacelessTranslationService.png'
    all_meta_types = ()

    security = ClassSecurityInfo()

    def __init__(self, default_domain='global', fallbacks=None):
        # We haven't specified that ITranslationServices have a default
        # domain.  So far, we've required the domain argument to .translate()
        self._domain = default_domain
        # _catalogs maps (language, domain) to identifiers
        catalogRegistry = {}
        fbcatalogRegistry = {}
        # What languages to fallback to, if there is no catalog for the
        # requested language (no fallback on individual messages)
        if fallbacks is None:
            fallbacks = LANGUAGE_FALLBACKS
        self._fallbacks = fallbacks

    def _registerMessageCatalog(self, catalog):
        # dont register broken message catalogs
        if isinstance(catalog, BrokenMessageCatalog):
            return

        domain = catalog.getDomain()
        language = catalog.getLanguage()
        catalogRegistry.setdefault((language, domain), []).append(catalog.getIdentifier())
        for lang in catalog.getOtherLanguages():
            fbcatalogRegistry.setdefault((lang, domain), []).append(catalog.getIdentifier())
        self._p_changed = 1

    def _unregister_inner(self, catalog, clist):
        for key, combo in clist.items():
            try:
                combo.remove(catalog.getIdentifier())
            except ValueError:
                continue
            if not combo: # removed the last catalog for a
                          # language/domain combination
                del clist[key]

    def _unregisterMessageCatalog(self, catalog):
        self._unregister_inner(catalog, catalogRegistry)
        self._unregister_inner(catalog, fbcatalogRegistry)
        self._p_changed = 1

    security.declarePrivate('calculatePoId')
    def calculatePoId(self, name, popath, language=None, domain=None):
        """Calulate the po id
        """
        # instance, software and global catalog path for i18n and locales
        iPath       = os.path.join(Globals.INSTANCE_HOME, 'Products') + os.sep
        sPath       = os.path.join(Globals.SOFTWARE_HOME, 'Products') + os.sep
        gci18nNPath = os.path.join(Globals.INSTANCE_HOME, 'i18n')
        gcLocPath   = os.path.join(Globals.INSTANCE_HOME, 'locales')

        # a global catalog is
        isGlobalCatalog = False

        # remove [isg]Path from the popath
        if popath.startswith(iPath):
            path = popath[len(iPath):]
        elif popath.startswith(sPath):
            path = popath[len(sPath):]
        elif popath.startswith(gci18nNPath):
            path = popath[len(gci18nNPath):]
            isGlobalCatalog = True
        elif popath.startswith(gcLocPath):
            path = popath[len(gcLocPath):]
            isGlobalCatalog = True
        else:
            # po file is located at a strange place calculate the name using
            # the position of the i18n/locales directory
            p = popath.split(os.sep)
            try:
                idx = p.index('i18n')
            except ValueError:
                try:
                    idx = p.index('locales')
                except ValueError:
                    raise OSError('Invalid po path %s for %s. That should not happen' % (popath, name))
            path = os.path.join(p[idx-1],p[idx])

        # the po file name is GlobalCatalogs-$name or MyProducts.i18n-$name
        # or MyProducts.locales-$name
        if not isGlobalCatalog:
            p = path.split(os.sep)
            pre = '.'.join(p[:2])
        else:
            pre = 'GlobalCatalogs'

        if '.egg' in popath:
            try:
                pre = popath[:popath.index('.egg')].split(os.sep)[-1].split('-')[0]
            except Exception, e:
                pass

        if language and domain:
            return "%s-%s-%s.po" % (pre, language, domain)
        else:
            return '%s-%s' % (pre, name)

    def _load_catalog_file(self, name, popath, language=None, domain=None):
        """Create catalog instances in ZODB"""
        id = self.calculatePoId(name, popath, language=language, domain=domain)

        # validate id
        try:
            self._checkId(id, 1)
        except:
            id=name # fallback mode for borked paths

        # the po file path
        pofile = os.path.join(popath, name)

        ob = self._getOb(id, _marker)
        try:
            if isinstance(ob, BrokenMessageCatalog):
                # remove broken catalog
                self._delObject(id)
                ob = _marker
        except:
            pass
        try:
            if ob is _marker:
                self.addCatalog(GettextMessageCatalog(id, pofile, language, domain))
            else:
                self.reloadCatalog(ob)
        except IOError:
            # io error probably cause of missing or not accessable
            try:
                # remove false catalog from PTS instance
                self._delObject(id)
            except:
                pass
        except KeyboardInterrupt:
            raise
        except:
            exc=sys.exc_info()
            log('Message Catalog has errors', logging.WARNING, pofile, exc)

    def _load_i18n_dir(self, basepath):
        """Loads an i18n directory (Zope3 PTS format)."""
        _load_i18n_dir(basepath)

    def _updateMoFile(self, name, msgpath, lang, domain):
        """Creates or updates a mo file in the locales folder."""
        mofile = join(msgpath, name[:-2] + 'mo')
        return _updateMoFile(name, msgpath, lang, domain, mofile)

    def _register_catalog_file(self, name, msgpath, lang, domain, update=False):
        """Registers a catalog file as an ITranslationDomain."""
        _register_catalog_file(name, msgpath, lang, domain, update=update)

    security.declareProtected(view_management_screens, 'manage_renameObject')
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """
        wrap manage_renameObject to deal with registration
        """
        catalog = self._getOb(id)
        self._unregisterMessageCatalog(catalog)
        Folder.manage_renameObject(self, id, new_id, REQUEST=None)
        self._registerMessageCatalog(catalog)

    def _delObject(self, id, dp=1):
        catalog = self._getOb(id)
        Folder._delObject(self, id, dp)
        self._unregisterMessageCatalog(catalog)

    security.declarePrivate('reloadCatalog')
    def reloadCatalog(self, catalog):
        # trigger an exception if we don't know anything about it
        id=catalog.id
        self._getOb(id)
        self._unregisterMessageCatalog(catalog)
        catalog.reload()
        catalog=self._getOb(id)
        self._registerMessageCatalog(catalog)

    security.declarePrivate('addCatalog')
    def addCatalog(self, catalog):
        try:
            self._delObject(catalog.id)
        except:
            pass
        lang = catalog.getLanguage()
        if not _checkLanguage(lang):
            return
        self._setObject(catalog.id, catalog, set_owner=False)
        log('adding %s: %s' % (catalog.id, catalog.title))
        self._registerMessageCatalog(catalog)

    security.declarePrivate('getCatalogsForTranslation')
    @memoize
    def getCatalogsForTranslation(self, request, domain, target_language=None):
        if target_language is None:
            target_language = self.negotiate_language(request, domain)

        # get the catalogs for translations
        catalog_names = catalogRegistry.get((target_language, domain), ()) or \
                        fbcatalogRegistry.get((target_language, domain), ())
        catalog_names = list(catalog_names)

        # get fallback catalogs
        for language in self._fallbacks:
            fallback_catalog_names = catalogRegistry.get((language, domain),  ())
            if fallback_catalog_names:
                for fallback_catalog_name in fallback_catalog_names:
                    if fallback_catalog_name not in catalog_names:
                        catalog_names.append(fallback_catalog_name)

        # move global catalogs to the beginning to allow overwriting
        # message ids by placing a po file in INSTANCE_HOME/i18n
        # use pos to keep the sort order
        pos=0
        for i in range(len(catalog_names)):
            catalog_name = catalog_names[i]
            if catalog_name.startswith('GlobalCatalogs-'):
                del catalog_names[i]
                catalog_names.insert(pos, catalog_name)
                pos+=1

        # test for right to left language
        if not request.has_key(PTS_IS_RTL):
            request.set(PTS_IS_RTL, False)
        for name in catalog_names:
            if rtlRegistry.get(name):
                request.set(PTS_IS_RTL, True)
                break

        return [translationRegistry[name] for name in catalog_names]

    security.declarePrivate('setLanguageFallbacks')
    def setLanguageFallbacks(self, fallbacks=None):
        if fallbacks is None:
            fallbacks = LANGUAGE_FALLBACKS
        self._fallbacks = fallbacks

    security.declareProtected(view, 'getLanguageName')
    def getLanguageName(self, code):
        for (ccode, cdomain), cnames in catalogRegistry.items():
            if ccode == code:
                for cname in cnames:
                    cat = self._getOb(cname)
                    if cat.name:
                        return cat.name

    security.declareProtected(view, 'getLanguages')
    def getLanguages(self, domain=None):
        """
        Get available languages
        """
        if domain is None:
            # no domain, so user wants 'em all
            langs = catalogRegistry.keys()
            # uniquify
            d = {}
            for l in langs:
                d[l[0]] = 1
            l = d.keys()
        else:
            l = [k[0] for k in catalogRegistry.keys() if k[1] == domain]
        l.sort()
        return l

    security.declareProtected(view, 'translate')
    def translate(self, domain, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        # Translate a message using Unicode.
        if not msgid:
            # refuse to translate an empty msgid
            return default

        # ZPT passes the object as context.  That's wrong according to spec.
        if not IBrowserRequest.providedBy(context):
            context = aq_acquire(context, 'REQUEST')
        text = msgid

        return z3translate(msgid, domain, mapping, context,
                           target_language, default)

    security.declarePrivate('negotiate_language')
    @memoize
    def negotiate_language(self, request, domain):
        langs = [m[0] for m in catalogRegistry.keys() if m[1] == domain] + \
                [m[0] for m in fbcatalogRegistry.keys() if m[1] == domain]
        for fallback in self._fallbacks:
            if fallback not in langs:
                langs.append(fallback)
        return negotiator.negotiate(langs, request, 'language')

    security.declareProtected(view, 'getDomain')
    def getDomain(self, domain):
        """
        return a domain instance
        """
        return Domain(domain, self)

    security.declarePrivate('interpolate')
    def interpolate(self, text, mapping):
        """
        Insert the data passed from mapping into the text
        """
        # If the mapping does not exist or is empty, make a
        # "raw translation" without interpolation.
        if not mapping:
            return text

        return z3interpolate(text, mapping=mapping)

    security.declareProtected(view_management_screens, 'manage_main')
    def manage_main(self, REQUEST, *a, **kw):
        """
        Wrap Folder's manage_main to render international characters
        """
        # ugh, API cruft
        if REQUEST is self and a:
            REQUEST = a[0]
            a = a[1:]
        # wrap the special dtml method Folder.manage_main into a valid
        # acquisition context. Required for Zope 2.8+.
        try:
            r = Folder.manage_main(self, self, REQUEST, *a, **kw)
        except AttributeError:
            manage_main = ImplicitAcquisitionWrapper(Folder.manage_main, self)
            r = manage_main(self, self, REQUEST, *a, **kw)
        if isinstance(r, unicode):
            r = r.encode('utf-8')
        REQUEST.RESPONSE.setHeader('Content-type', 'text/html; charset=utf-8')
        return r

InitializeClass(PlacelessTranslationService)


zope.deprecation.deprecated(
   ('PlacelessTranslationService', 'PTSWrapper', 'PTS_IS_RTL', 'NAME_RE',
    'LANGUAGE_FALLBACKS', '_get_var_regex', '_interp_regex', 'catalogRegistry',
    'registerCatalog', 'fbcatalogRegistry', 'registerFBCatalog'),
    "The PlacelessTranslationService itself is deprecated and will be "
    "removed in the next major version of PTS."
   )
