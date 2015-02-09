# Patch the Zope3 negotiator to cache the negotiated languages
from Products.PlacelessTranslationService.memoize import memoize_second
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.negotiator import Negotiator
from zope.i18n.negotiator import normalize_langs

TEMPLATE_LANGUAGE = ['en']

def getLanguage(self, langs, env):
    envadapter = IUserPreferredLanguages(env)
    userlangs = envadapter.getPreferredLanguages()
    # Always add the template language to the available ones. This allows the
    # template language to be picked without the need for a message catalog
    # for every domain for it to be registered.
    langs = list(langs) + TEMPLATE_LANGUAGE
    # Prioritize on the user preferred languages.  Return the
    # first user preferred language that the object has available.
    langs = normalize_langs(langs)
    for lang in userlangs:
        if lang in langs:
            return langs.get(lang)
        # If the user asked for a specific variation, but we don't
        # have it available we may serve the most generic one,
        # according to the spec (eg: user asks for ('en-us',
        # 'de'), but we don't have 'en-us', then 'en' is preferred
        # to 'de').
        parts = lang.split('-')
        if len(parts) > 1 and parts[0] in langs:
            return langs.get(parts[0])
    return None

Negotiator.getLanguage = memoize_second(getLanguage)


# Patch Zope3 to use a lazy message catalog, but only if we haven't
# restricted the available catalogs in the first place.
from Products.PlacelessTranslationService.load import PTS_LANGUAGES
if PTS_LANGUAGES is None:
    from zope.i18n import gettextmessagecatalog
    from Products.PlacelessTranslationService.lazycatalog import \
        LazyGettextMessageCatalog
    gettextmessagecatalog.GettextMessageCatalog = LazyGettextMessageCatalog
