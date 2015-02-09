
# ##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""This module handles the 'i18n' namespace directives.
"""
__docformat__ = 'restructuredtext'

import os

from zope.component import getSiteManager
from zope.component import queryUtility
from zope.component.interface import provideInterface
from zope.configuration.fields import Path
from zope.interface import Interface

from zope.i18n import config
from zope.i18n.compile import compile_mo_file
from zope.i18n.gettextmessagecatalog import GettextMessageCatalog
from zope.i18n.testmessagecatalog import TestMessageCatalog
from zope.i18n.translationdomain import TranslationDomain
from zope.i18n.interfaces import ITranslationDomain


class IRegisterTranslationsDirective(Interface):
    """Register translations with the global site manager."""

    directory = Path(
        title=u"Directory",
        description=u"Directory containing the translations",
        required=True
        )


def allow_language(lang):
    if config.ALLOWED_LANGUAGES is None:
        return True
    return lang in config.ALLOWED_LANGUAGES


def handler(catalogs, name):
    """ special handler handling the merging of two message catalogs """
    gsm = getSiteManager()
    # Try to get an existing domain and add the given catalogs to it
    domain = queryUtility(ITranslationDomain, name)
    if domain is None:
        domain = TranslationDomain(name)
        gsm.registerUtility(domain, ITranslationDomain, name=name)
    for catalog in catalogs:
        domain.addCatalog(catalog)
    # make sure we have a TEST catalog for each domain:
    domain.addCatalog(TestMessageCatalog(name))


def registerTranslations(_context, directory):
    path = os.path.normpath(directory)
    domains = {}

    # Gettext has the domain-specific catalogs inside the language directory,
    # which is exactly the opposite as we need it. So create a dictionary that
    # reverses the nesting.
    for language in os.listdir(path):
        if not allow_language(language):
            continue
        lc_messages_path = os.path.join(path, language, 'LC_MESSAGES')
        if os.path.isdir(lc_messages_path):
            # Preprocess files and update or compile the mo files
            if config.COMPILE_MO_FILES:
                for domain_file in os.listdir(lc_messages_path):
                    if domain_file.endswith('.po'):
                        domain = domain_file[:-3]
                        compile_mo_file(domain, lc_messages_path)
            for domain_file in os.listdir(lc_messages_path):
                if domain_file.endswith('.mo'):
                    domain_path = os.path.join(lc_messages_path, domain_file)
                    domain = domain_file[:-3]
                    if not domain in domains:
                        domains[domain] = {}
                    domains[domain][language] = domain_path

    # Now create TranslationDomain objects and add them as utilities
    for name, langs in domains.items():
        catalogs = []
        for lang, file in langs.items():
            catalogs.append(GettextMessageCatalog(lang, name, file))
        # register the necessary actions directly (as opposed to using
        # `zope.component.zcml.utility`) since we need the actual utilities
        # in place before the merging can be done...
        _context.action(
            discriminator = None,
            callable = handler,
            args = (catalogs, name))

    # also register the interface for the translation utilities
    provides = ITranslationDomain
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (provides.__module__ + '.' + provides.getName(), provides))
