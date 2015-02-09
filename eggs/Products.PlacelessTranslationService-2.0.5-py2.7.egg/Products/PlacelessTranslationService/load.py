import fnmatch
import logging
import os
from os.path import join
import shutil
from stat import ST_MTIME

from pythongettext.msgfmt import Msgfmt
from pythongettext.msgfmt import PoSyntaxError
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.i18n.gettextmessagecatalog import GettextMessageCatalog
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.translationdomain import TranslationDomain

from Products.PlacelessTranslationService.utils import log
from Products.PlacelessTranslationService.lazycatalog import \
    LazyGettextMessageCatalog

# Restrict languages
PTS_LANGUAGES = None
if bool(os.getenv('PTS_LANGUAGES')):
    langs = os.getenv('PTS_LANGUAGES')
    langs = langs.strip().replace(',', '').split()
    PTS_LANGUAGES = tuple(langs)


def _checkLanguage(lang):
    if PTS_LANGUAGES is None:
        return True
    else:
        return bool(lang in PTS_LANGUAGES)


def _load_i18n_dir(basepath):
    """
    Loads an i18n directory (Zope3 PTS format)
    Format:
        Products/MyProduct/i18n/*.po
    The language and domain are stored in the po file
    """
    # load po files
    basepath = os.path.normpath(basepath)
    log('Looking for po files in ' + basepath, logging.DEBUG)
    names = fnmatch.filter(os.listdir(basepath), '*.po')
    if not names:
        log('Nothing found in ' + basepath, logging.DEBUG)
        return

    registered = []

    for name in names:
        lang = None
        domain = None
        pofile = join(basepath, name)
        po = Msgfmt(pofile, None)
        po.read(header_only=True)
        header = po.messages.get('', None)
        if header is not None:
            mime_header = {}
            pairs = [l.split(':', 1) for l in header.split('\n') if l]
            for key, value in pairs:
                mime_header[key.strip().lower()] = value.strip()
            lang = mime_header.get('language-code', None)
            domain = mime_header.get('domain', None)
            if lang is not None and domain is not None:
                if _checkLanguage(lang):
                    reg = (name, basepath, lang, domain, True)
                    _register_catalog_file(*reg)
                    registered.append(name)

    log('Initialized:', detail = str(len(registered)) +
        (' message catalogs in %s\n' % basepath))

def _updateMoFile(name, msgpath, lang, domain, mofile):
    """
    Creates or updates a mo file in the locales folder. Returns True if a
    new file was created.
    """
    pofile = join(msgpath, name)
    create = False
    update = False

    try:
        po_mtime = os.stat(pofile)[ST_MTIME]
    except (IOError, OSError):
        po_mtime = 0

    if os.path.exists(mofile):
        # Update mo file?
        try:
            mo_mtime = os.stat(mofile)[ST_MTIME]
        except (IOError, OSError):
            mo_mtime = 0

        if po_mtime > mo_mtime:
            # Update mo file
            update = True
        else:
            # Mo file is current
            return
    else:
        # Create mo file
        create = True

    if create or update:
        try:
            mo = Msgfmt(pofile, domain).getAsFile()
            fd = open(mofile, 'wb')
            fd.write(mo.read())
            fd.close()

        except (IOError, OSError, PoSyntaxError):
            log('Error while compiling %s' % pofile, logging.WARNING)
            return

        if create:
            return True

    return None

def _register_catalog_file(name, msgpath, lang, domain, update=False):
    """Registers a catalog file as an ITranslationDomain."""
    if not _checkLanguage(lang):
        return
    mofile = join(msgpath, name[:-2] + 'mo')
    result = _updateMoFile(name, msgpath, lang, domain, mofile)
    if result or update:
        # Newly created file or one from a i18n folder,
        # the Z3 domain utility does not exist
        if queryUtility(ITranslationDomain, name=domain) is None:
            ts_domain = TranslationDomain(domain)
            sm = getGlobalSiteManager()
            sm.registerUtility(ts_domain, ITranslationDomain, name=domain)

        util = queryUtility(ITranslationDomain, name=domain)
        if util is not None and os.path.exists(mofile):
            if PTS_LANGUAGES is not None:
                # If we have restricted the available languages,
                # use the speed and not memory optimized version
                cat = GettextMessageCatalog(lang, domain, mofile)
            else:
                # Otherwise optimize for memory footprint
                cat = LazyGettextMessageCatalog(lang, domain, mofile)
            # Add message catalog
            util.addCatalog(cat)

def _remove_mo_cache(path=None):
    """Remove the mo cache."""
    if path is not None and os.path.exists(path):
        if not os.access(path, os.W_OK):
            log("No write permission on folder %s" % path, logging.INFO)
            return False
        shutil.rmtree(path)
