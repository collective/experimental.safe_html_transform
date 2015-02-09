from zope.interface import Interface
from zope.i18n.interfaces import ITranslationDomain

class IPlacelessTranslationService(Interface):
    """The PlacelessTranslationService.
    """

class IPTSTranslationDomain(ITranslationDomain):
    """Marker for PTS surrogate domains"""
