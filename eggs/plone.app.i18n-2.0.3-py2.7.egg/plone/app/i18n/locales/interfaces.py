from plone.i18n.locales.interfaces import ICountryAvailability
from plone.i18n.locales.interfaces import IContentLanguageAvailability
from plone.i18n.locales.interfaces import IMetadataLanguageAvailability
from plone.i18n.locales.interfaces import IModifiableCountryAvailability
from plone.i18n.locales.interfaces import IModifiableLanguageAvailability


class ICountries(ICountryAvailability, IModifiableCountryAvailability):
    """A modifiable list of countries."""


class IContentLanguages(IContentLanguageAvailability,
                        IModifiableLanguageAvailability):
    """A modifiable list of available content languages."""


class IMetadataLanguages(IMetadataLanguageAvailability,
                         IModifiableLanguageAvailability):
    """A modifiable list of available metadata languages."""
