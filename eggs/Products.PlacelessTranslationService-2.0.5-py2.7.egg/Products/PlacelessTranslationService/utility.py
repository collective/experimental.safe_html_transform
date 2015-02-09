import zope.deprecation

from zope.interface import implements
from zope.component import queryUtility
from zope.i18n import interpolate

from ZODB.POSException import ConnectionStateError

from interfaces import IPlacelessTranslationService
from interfaces import IPTSTranslationDomain


class PTSTranslationDomain(object):
    """Makes translation domains that are still kept in PTS available as
    ITranslationDomain utilities. That way they are usable from Zope 3 code
    such as Zope 3 PageTemplates."""

    implements(IPTSTranslationDomain)

    def __init__(self, domain):
        self.domain = domain

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        pts = queryUtility(IPlacelessTranslationService)
        try:
            if pts is not None:
                return pts.translate(self.domain, msgid, mapping, context,
                                     target_language, default)
        except ConnectionStateError:
            pass

        return interpolate(default, mapping)


zope.deprecation.deprecated(
   ('PTSTranslationDomain', ),
    "PlacelessTranslationService.PTSTranslationDomain is deprecated and will "
    "be removed in the next major version of PTS."
   )
