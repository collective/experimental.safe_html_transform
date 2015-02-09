"""A simple implementation of a Message Catalog.
"""

from gettext import GNUTranslations
import os, sys, types, traceback
import logging
from stat import ST_MTIME

from pythongettext.msgfmt import Msgfmt

import zope.deprecation

from Acquisition import aq_parent, Implicit
from DateTime import DateTime
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens
from App.class_init import InitializeClass
from Globals import INSTANCE_HOME
from App.Common import package_home
import Globals
from OFS.Traversable import Traversable
from Persistence import Persistent
from App.Management import Tabs

from Products.PlacelessTranslationService import CACHE_PATH
from Products.PlacelessTranslationService.load import _remove_mo_cache
from Products.PlacelessTranslationService.utils import (
    log, make_relative_location, Registry)

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

def ptFile(id, *filename):
    if type(filename[0]) is types.DictType:
        filename = list(filename)
        filename[0] = package_home(filename[0])
    filename = os.path.join(*filename)
    if not os.path.splitext(filename)[1]:
        filename = filename + '.pt'
    return PageTemplateFile(filename, '', __name__=id)

permission = 'View management screens'

translationRegistry = Registry()
registerTranslation = translationRegistry.register
rtlRegistry = Registry()
registerRTL = rtlRegistry.register

def getMessage(catalog, id, orig_text=None):
    """get message from catalog

    returns the message according to the id 'id' from the catalog 'catalog' or
    raises a KeyError if no translation was found. The return type is always
    unicode
    """
    msg = catalog.gettext(id)
    if msg is id:
        raise KeyError
    if type(msg) is types.StringType:
        msg = unicode(msg, catalog._charset)
    return msg


class BrokenMessageCatalog(Persistent, Implicit, Traversable, Tabs):
    """ broken message catalog """
    meta_type = title = 'Broken Gettext Message Catalog'
    icon='p_/broken'

    isPrincipiaFolderish = 0
    isTopLevelPrincipiaApplicationObject = 0

    security = ClassSecurityInfo()
    security.declareObjectProtected(view_management_screens)

    def __init__(self, id, pofile, error):
        self._pofile = make_relative_location(pofile)
        self.id = id
        self._mod_time = self._getModTime()
        self.error = traceback.format_exception(error[0],error[1],error[2])

    # modified time helper
    def _getModTime(self):
        """
        """
        try:
            mtime = os.stat(self._getPoFile())[ST_MTIME]
        except (IOError, OSError):
            mtime = 0
        return mtime

    def getIdentifier(self):
        """
        """
        return self.id

    def getId(self):
        """
        """
        return self.id

    security.declareProtected(view_management_screens, 'getError')
    def getError(self):
        """
        """
        return self.error

    def _getPoFile(self):
        """get absolute path of the po file as string
        """
        prefix, pofile = self._pofile
        if prefix == 'ZOPE_HOME':
            return os.path.join(ZOPE_HOME, pofile)
        elif prefix == 'INSTANCE_HOME':
            return os.path.join(INSTANCE_HOME, pofile)
        else:
            return os.path.normpath(pofile)

    security.declareProtected(view_management_screens, 'Title')
    def Title(self):
        return self.title

    def get_size(self):
        """Get the size of the underlying file."""
        return os.path.getsize(self._getPoFile())

    def reload(self, REQUEST=None):
        """ Forcibly re-read the file """
        # get pts
        pts = aq_parent(self)
        name = self.getId()
        pofile = self._getPoFile()
        pts._delObject(name)
        try: pts.addCatalog(GettextMessageCatalog(name, pofile))
        except OSError:
            # XXX TODO
            # remove a catalog if it cannot be loaded from the old location
            raise
        except:
            exc=sys.exc_info()
            log('Message Catalog has errors', logging.WARNING, name, exc)
        self = pts._getOb(name)
        if hasattr(REQUEST, 'RESPONSE'):
            if not REQUEST.form.has_key('noredir'):
                REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declareProtected(view_management_screens, 'file_exists')
    def file_exists(self):
        try:
            file = open(self._getPoFile(), 'rb')
        except:
            return False
        return True

    def manage_afterAdd(self, item, container): pass
    def manage_beforeDelete(self, item, container): pass
    def manage_afterClone(self, item): pass

    manage_options = (
        {'label':'Info', 'action':''},
        )

    index_html = ptFile('index_html', globals(), 'www', 'catalog_broken')

InitializeClass(BrokenMessageCatalog)

class GettextMessageCatalog(Persistent, Implicit, Traversable, Tabs):
    """
    Message catalog that wraps a .po file in the filesystem and stores
    the compiled po file in the zodb
    """
    meta_type = title = 'Gettext Message Catalog'
    icon = 'misc_/PlacelessTranslationService/GettextMessageCatalog.png'

    isPrincipiaFolderish = 0
    isTopLevelPrincipiaApplicationObject = 0

    security = ClassSecurityInfo()
    security.declareObjectProtected(view_management_screens)

    def __init__(self, id, pofile, language=None, domain=None):
        """Initialize the message catalog"""
        self._pofile   = make_relative_location(pofile)
        self.id        = id
        self._mod_time = self._getModTime()
        self._language = language
        self._domain   = domain
        self._prepareTranslations(0)

    def _prepareTranslations(self, catch=1):
        """Try to generate the translation object
           if fails remove us from registry
        """
        try: self._doPrepareTranslations()
        except:
            if self.getId() in translationRegistry.keys():
                del translationRegistry[self.getId()]
            if not catch: raise
            else: pass

    def _doPrepareTranslations(self):
        """Generate the translation object from a po file
        """
        self._updateFromFS()
        tro = None
        if getattr(self, '_v_tro', None) is None:
            self._v_tro = tro = translationRegistry.get(self.getId(), None)
        if tro is None:
            moFile = self._getMoFile()
            tro = GNUTranslations(moFile)
            if not self._language:
                self._language = (tro._info.get('language-code', None) # new way
                               or tro._info.get('language', None)) # old way
            if not self._domain:
                self._domain = tro._info.get('domain', None)
            if self._language is None or self._domain is None:
                raise ValueError, 'potfile %s has no metadata, PTS needs a language and a message domain!' % os.path.join(*self._pofile)
            self._language = self._language.lower().replace('_', '-')
            self._other_languages = tro._info.get('x-is-fallback-for', '').split()
            self.preferred_encodings = tro._info.get('preferred-encodings', '').split()
            self.name = unicode(tro._info.get('language-name', ''), tro._charset)
            self.default_zope_data_encoding = tro._charset

            translationRegistry[self.getId()] = self._v_tro = tro

            # right to left support
            is_rtl = tro._info.get('x-is-rtl', 'no').strip().lower()
            if is_rtl in ('yes', 'y', 'true', '1'):
                self._is_rtl = True
            elif is_rtl in ('no', 'n', 'false', '0'):
                self._is_rtl = False
            else:
                raise ValueError, 'Unsupported value for X-Is-RTL' % is_rtl
            rtlRegistry[self.getId()] = self.isRTL()

            if self.name:
                self.title = '%s language (%s) for %s' % (self._language, self.name, self._domain)
            else:
                self.title = '%s language for %s' % (self._language, self._domain)

    def filtered_manage_options(self, REQUEST=None):
        return self.manage_options

    def reload(self, REQUEST=None):
        """Forcibly re-read the file
        """
        if self.getId() in translationRegistry.keys():
            del translationRegistry[self.getId()]
        if hasattr(self, '_v_tro'):
            del self._v_tro
        name = self.getId()
        pts = aq_parent(self)
        pofile=self._getPoFile()
        try:
            self._prepareTranslations(0)
            log('reloading %s: %s' % (name, self.title), severity=logging.DEBUG)
        except:
            pts._delObject(name)
            exc=sys.exc_info()
            log('Message Catalog has errors', logging.WARNING, name, exc)
        self = pts._getOb(name)
        if hasattr(REQUEST, 'RESPONSE'):
            if not REQUEST.form.has_key('noredir'):
                REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declarePublic('queryMessage')
    def queryMessage(self, id, default=None):
        """Queries the catalog for a message

        If the message wasn't found the default value or the id is returned.
        """
        try:
            return getMessage(translationRegistry[self.getId()],id,default)
        except KeyError:
            if default is None:
                default = id
            return default

    def getLanguage(self):
        """
        """
        return self._language

    def getLanguageName(self):
        """
        """
        return self.name or self._language

    def getOtherLanguages(self):
        """
        """
        return self._other_languages

    def getDomain(self):
        """
        """
        return self._domain

    def getIdentifier(self):
        """
        """
        return self.id

    def getId(self):
        """
        """
        return self.id

    def getInfo(self, name):
        """
        """
        self._prepareTranslations()
        return self._v_tro._info.get(name, None)

    def isRTL(self):
        """
        """
        return self._is_rtl

    security.declareProtected(view_management_screens, 'Title')
    def Title(self):
        return self.title

    def _getMoFile(self):
        """get compiled version of the po file as file object
        """
        mo = Msgfmt(self._readFile(), self.getId())
        return mo.getAsFile()

    def _getPoFile(self):
        """get absolute path of the po file as string
        """
        prefix, pofile = self._pofile
        if prefix == 'ZOPE_HOME':
            return os.path.join(ZOPE_HOME, pofile)
        elif prefix == 'INSTANCE_HOME':
            return os.path.join(INSTANCE_HOME, pofile)
        else:
            return os.path.normpath(pofile)

    def _readFile(self, reparse=False):
        """Read the data from the filesystem.

        """
        file = open(self._getPoFile(), 'rb')
        data = []
        try:
            # XXX need more checks here
            data = file.readlines()
        finally:
            file.close()
        return data

    def _updateFromFS(self):
        """Refresh our contents from the filesystem

        if the file is newer and we are running in debug mode.
        """
        if Globals.DevelopmentMode:
            mtime = self._getModTime()
            if mtime != self._mod_time:
                self._mod_time = mtime
                self.reload()

    def _getModTime(self):
        """
        """
        try:
            mtime = os.stat(self._getPoFile())[ST_MTIME]
        except (IOError, OSError):
            mtime = 0
        return mtime

    def get_size(self):
        """Get the size of the underlying file."""
        return os.path.getsize(self._getPoFile())

    def getModTime(self):
        """Return the last_modified date of the file we represent.

        Returns a DateTime instance.
        """
        self._updateFromFS()
        return DateTime(self._mod_time)

    def getObjectFSPath(self):
        """Return the path of the file we represent"""
        return self._getPoFile()

    # Zope/OFS integration

    def manage_afterAdd(self, item, container): pass
    def manage_beforeDelete(self, item, container): pass
    def manage_afterClone(self, item): pass

    manage_options = (
        {'label':'Info', 'action':''},
        {'label':'Test', 'action':'zmi_test'},
        )

    index_html = ptFile('index_html', globals(), 'www', 'catalog_info')
    zmi_test = ptFile('zmi_test', globals(), 'www', 'catalog_test')

    security.declareProtected(view_management_screens, 'file_exists')
    def file_exists(self):
        try:
            file = open(self._getPoFile(), 'rb')
        except:
            return False
        return True

    security.declareProtected(view_management_screens, 'getEncoding')
    def getEncoding(self):
        try:
            content_type = self.getHeader('content-type')
            enc = content_type.split(';')[1].strip()
            enc = enc.split('=')[1]
        except: enc='utf-8'
        return enc

    def getHeader(self, header):
        self._prepareTranslations()
        info = self._v_tro._info
        return info.get(header)

    security.declareProtected(view_management_screens, 'displayInfo')
    def displayInfo(self):
        self._prepareTranslations()
        try: info = self._v_tro._info
        except:
            # broken catalog probably
            info={}
        keys = info.keys()
        keys.sort()
        return [{'name': k, 'value': info[k]} for k in keys] + [
            {'name': 'full path', 'value': os.path.join(*self._pofile)},
            {'name': 'last modification', 'value': self.getModTime().ISO()}
            ]

InitializeClass(GettextMessageCatalog)


class MoFileCache(object):
    """Cache for mo files
    """

    def __init__(self, path=None):
        self._path = path

    def storeMoFile(self, catalog):
        """compile and save to mo file for catalog to disk."""
        return None

    def retrieveMoFile(self, catalog):
        """Load a mo file file for a catalog from disk."""
        return None

    def getPath(self, catalog):
        """Get the mo file path (cache path + file name)."""
        return None

    def isCacheHit(self, catalog):
        """Cache hit?"""
        return None

    def compilePo(self, catalog):
        """Compile a po file to mo. Returns a file handler."""
        mo = Msgfmt(catalog._readFile(), catalog.getId())
        return mo.getAsFile()

    def cachedPoFile(self, catalog):
        """Cache a po file (public api)."""
        return None, self.compilePo(catalog)

    def purgeCache(self):
        """Purge the cache and remove all compiled mo files."""
        return _remove_mo_cache(CACHE_PATH)


_moCache = MoFileCache()
cachedPoFile = _moCache.cachedPoFile
purgeMoFileCache = _moCache.purgeCache

zope.deprecation.deprecated(
   ('MoFileCache', 'GettextMessageCatalog', 'BrokenMessageCatalog',
    'cachedPoFile', 'purgeMoFileCache', 'ptFile', 'getMessage'),
    "PlacelessTranslationService's implementation of Message catalogs and "
    "the MoFileCache is deprecated and will be removed in the next major "
    "version of PTS."
   )
