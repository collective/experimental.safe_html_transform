# -*- coding: UTF-8 -*-

from plone.app.i18n.locales.interfaces import ICountries
from plone.i18n.locales.countries import CountryAvailability

from zope.interface import implements

from OFS.SimpleItem import SimpleItem


class Countries(SimpleItem, CountryAvailability):
    """A local utility storing a list of available countries.

    Let's make sure that this implementation actually fulfills the API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(ICountries, Countries)
      True
    """
    implements(ICountries)

    id = 'plone_app_countries'
    title = 'Manages available countries'
    meta_type = 'Plone App I18N Countries'

    def __init__(self):
        self.countries = ['en']

    def getAvailableCountries(self):
        """Return a sequence of country tags for available countries.
        """
        return list(self.countries)

    def setAvailableCountries(self, countries):
        """Set a list of available country tags.
        """
        countries = list(countries)
        self.countries = countries
