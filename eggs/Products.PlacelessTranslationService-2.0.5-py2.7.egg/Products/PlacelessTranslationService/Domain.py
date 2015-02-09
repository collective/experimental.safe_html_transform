import zope.deprecation
from zope.i18n import translate as z3translate


class Domain:

    def __init__(self, domain, service):
        self._domain = domain
        self._translationService = service

    def getDomainName(self):
        """Return the domain name"""
        return self._domain

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None):
        return z3translate(msgid, self._domain, mapping, context,
                           target_language)


zope.deprecation.deprecated(
   ('Domain', ),
    "PlacelessTranslationService.Domain is deprecated and will be "
    "removed in the next major version of PTS."
   )
