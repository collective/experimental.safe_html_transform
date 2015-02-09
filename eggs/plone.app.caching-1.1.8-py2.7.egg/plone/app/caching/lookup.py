from zope.interface import implements
from zope.component import queryUtility

from plone.registry.interfaces import IRegistry

from z3c.caching.registry import lookup
from plone.caching.interfaces import IRulesetLookup
from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import aq_base

from plone.app.caching.utils import getObjectDefaultView

class ContentItemLookup(object):
    """General lookup for browser views and page templates.

    1. Attempt to look up a ruleset using z3c.caching.registry.lookup()
       and return that if found (this is necessary because this adapter will
       override the default lookup in most cases).

    2. Get the name of the published object (i.e. the name of the view or
       page template).

    3. Otherwise, look up the published name in the page template mapping (as
       PageTemplateLookup does now) and return that if found

    4. Find the parent of the published object, possibly a content object.

       4.1. If the parent is a content object:
       4.1.1. Get the default view of the parent content object
       4.1.2. If the name of the published object is the same as the default
              view of the parent:
       4.1.2.1. Otherwise, look up the parent type in the content type mapping
                and return that if found
       4.1.2.2. Look up a ruleset on the parent object and return if that
                matches

    The template mapping is:

    ``plone.app.caching.interfaces.IPloneCacheSettings.templateRulesetMapping``

    The content type mapping is:

    ``plone.app.caching.interfaces.IPloneCacheSettings.contentTypeRulesetMapping``.

    Note that this lookup is *not* invoked for a view which happens to use a
    page template to render itself.
    """

    implements(IRulesetLookup)

    # This adapter is registered twice in configure.zcml, ala:
    # adapts(IPageTemplate, Interface)
    # adapts(IBrowserView, Interface)

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):

        # 1. Attempt to look up a ruleset using the default lookup
        ruleset = lookup(self.published)
        if ruleset is not None:
            return ruleset

        registry = queryUtility(IRegistry)
        if registry is None:
            return None

        ploneCacheSettings = registry.forInterface(IPloneCacheSettings, check=False)

        # 2. Get the name of the published object
        name = getattr(self.published, '__name__', None)
        if name is None:
            return None

        # 3. Look up the published name in the page template mapping
        if ploneCacheSettings.templateRulesetMapping is not None:
            ruleset = ploneCacheSettings.templateRulesetMapping.get(name, None)
            if ruleset is not None:
                return ruleset

        # 4. Find the parent of the published object
        parent = getattr(self.published, '__parent__', None)
        if parent is not None:

            # 4.1. If the parent is a content object:
            parentPortalType = getattr(aq_base(parent), 'portal_type', None)
            if parentPortalType is not None:

                # 4.1.1. Get the default view of the parent content object
                defaultView = getObjectDefaultView(parent)

                # 4.1.2. If the name of the published object is the same as the default view of the parent:
                if defaultView == name:

                    # 4.1.2.1. Look up the parent type in the content type mapping
                    if ploneCacheSettings.contentTypeRulesetMapping is not None:
                        ruleset = ploneCacheSettings.contentTypeRulesetMapping.get(parentPortalType, None)
                        if ruleset is not None:
                            return ruleset

                    # 4.1.2.2. Look up a ruleset on the parent object and return
                    ruleset = lookup(parent)
                    if ruleset is not None:
                        return ruleset

        return None
