# -*- coding: UTF-8 -*-

from plone.app.i18n.locales.interfaces import IContentLanguages
from plone.app.i18n.locales.interfaces import IMetadataLanguages
from plone.app.i18n.locales.interfaces import IModifiableLanguageAvailability

from plone.i18n.locales.languages import ContentLanguageAvailability
from plone.i18n.locales.languages import MetadataLanguageAvailability
from plone.i18n.locales.languages import LanguageAvailability

from zope.interface import implements

from OFS.SimpleItem import SimpleItem


class Languages(SimpleItem, LanguageAvailability):
    """ A base implementation for persistent utilities implementing
    IModifiableLanguageAvailability.

    Let's make sure that this implementation actually fulfills the API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IModifiableLanguageAvailability, Languages)
      True
    """
    implements(IModifiableLanguageAvailability)

    def __init__(self):
        self.languages = ['en']
        self.combined = []

    def getAvailableLanguages(self, combined=False):
        """Returns a sequence of language tags for available languages.
        """
        if combined:
            languages = list(self.languages)
            languages.extend(self.combined)
            return languages
        else:
            return list(self.languages)

    def setAvailableLanguages(self, languages, combined=False):
        """Sets a list of available language tags.
        """
        languages = list(languages)
        if combined:
            self.combined = languages
        else:
            self.languages = languages


class ContentLanguages(Languages, ContentLanguageAvailability):
    """A local utility storing a list of available content languages.

    Let's make sure that this implementation actually fulfills the API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IContentLanguages, ContentLanguages)
      True
    """
    implements(IContentLanguages)

    id = 'plone_app_content_languages'
    title = 'Manages available content languages'
    meta_type = 'Plone App I18N Content Languages'


class MetadataLanguages(Languages, MetadataLanguageAvailability):
    """A local utility storing a list of available metadata languages.

    Let's make sure that this implementation actually fulfills the API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IMetadataLanguages, MetadataLanguages)
      True
    """
    implements(IMetadataLanguages)

    id = 'plone_app_metadata_languages'
    title = 'Manages available metadata languages'
    meta_type = 'Plone App I18N Metadata Languages'
