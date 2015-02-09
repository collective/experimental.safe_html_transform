from Acquisition import aq_get
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.site.hooks import getSite
from zope.i18n import translate

from Products.CMFCore.utils import getToolByName


def getAllowedContentTypes(context):
    """ computes the list of allowed content types by subtracting the site property blacklist
        from the list of installed types.
    """
    allowable_types = getAllowableContentTypes(context)
    forbidden_types = getForbiddenContentTypes(context)
    allowed_types = [type for type in allowable_types if type not in forbidden_types]
    return allowed_types


def getAllowableContentTypes(context):
    """ retrieves the list of installed content types by querying portal transforms. """
    portal_transforms = getToolByName(context, 'portal_transforms')
    return portal_transforms.listAvailableTextInputs()


def getForbiddenContentTypes(context):
    """ Convenence method for retrevng the site property 'forbidden_contenttypes'."""
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            if site_properties.hasProperty('forbidden_contenttypes'):
                return list(site_properties.getProperty('forbidden_contenttypes'))
    return []


class AllowableContentTypesVocabulary(object):
    """Vocabulary factory for allowable content types.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool

      >>> name = 'plone.app.vocabularies.AllowableContentTypes'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> tool = DummyTool('portal_transforms')
      >>> def listAvailableTextInputs():
      ...     return ('text/plain', 'text/spam')
      >>> tool.listAvailableTextInputs = listAvailableTextInputs
      >>> context.portal_transforms = tool

      >>> types = util(context)
      >>> types
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(types.by_token)
      2

      >>> doc = types.by_token['text/plain']
      >>> doc.title, doc.token, doc.value
      ('text/plain', 'text/plain', 'text/plain')
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        items = list(getAllowableContentTypes(site))
        if 'text/x-plone-outputfilters-html' in items:
            items.remove('text/x-plone-outputfilters-html')
        items.sort()
        items = [SimpleTerm(i, i, i) for i in items]
        return SimpleVocabulary(items)

AllowableContentTypesVocabularyFactory = AllowableContentTypesVocabulary()


class AllowedContentTypesVocabulary(object):
    """Vocabulary factory for allowed content types.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool

      >>> name = 'plone.app.vocabularies.AllowedContentTypes'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> tool = DummyTool('portal_transforms')
      >>> def listAvailableTextInputs():
      ...     return ('text/plain', 'text/spam')
      >>> tool.listAvailableTextInputs = listAvailableTextInputs
      >>> context.portal_transforms = tool

      >>> tool = DummyTool('portal_properties')
      >>> class DummyProperties(object):
      ...     def hasProperty(self, value):
      ...         return True
      ...
      ...     def getProperty(self, value):
      ...         return ('text/spam', )
      >>> tool.site_properties = DummyProperties()
      >>> context.portal_properties = tool

      >>> types = util(context)
      >>> types
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(types.by_token)
      1

      >>> doc = types.by_token['text/plain']
      >>> doc.title, doc.token, doc.value
      ('text/plain', 'text/plain', 'text/plain')
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        items = list(getAllowedContentTypes(site))
        items.sort()
        items = [SimpleTerm(i, i, i) for i in items]
        return SimpleVocabulary(items)

AllowedContentTypesVocabularyFactory = AllowedContentTypesVocabulary()


class PortalTypesVocabulary(object):
    """Vocabulary factory for portal types.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTypeTool

      >>> name = 'plone.app.vocabularies.PortalTypes'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> context.portal_types = DummyTypeTool()
      >>> types = util(context)
      >>> types
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(types.by_token)
      2

      >>> doc = types.by_token['Document']
      >>> doc.title, doc.token, doc.value
      (u'Page', 'Document', 'Document')
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        ttool = getToolByName(site, 'portal_types', None)
        if ttool is None:
            return SimpleVocabulary([])

        request = aq_get(ttool, 'REQUEST', None)
        items = [(translate(ttool[t].Title(), context=request), t)
                 for t in ttool.listContentTypes()]
        items.sort()
        items = [SimpleTerm(i[1], i[1], i[0]) for i in items]
        return SimpleVocabulary(items)

PortalTypesVocabularyFactory = PortalTypesVocabulary()


class UserFriendlyTypesVocabulary(object):
    """Vocabulary factory for user friendly portal types.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool
      >>> from plone.app.vocabularies.tests.base import DummyTypeTool

      >>> name = 'plone.app.vocabularies.UserFriendlyTypes'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> context.portal_types = DummyTypeTool()
      >>> tool = DummyTool('plone_utils')
      >>> def getUserFriendlyTypes():
      ...     return ('Document', )
      >>> tool.getUserFriendlyTypes = getUserFriendlyTypes
      >>> context.plone_utils = tool

      >>> types = util(context)
      >>> types
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(types.by_token)
      1

      >>> doc = types.by_token['Document']
      >>> doc.title, doc.token, doc.value
      (u'Page', 'Document', 'Document')
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        ptool = getToolByName(site, 'plone_utils', None)
        ttool = getToolByName(site, 'portal_types', None)
        if ptool is None or ttool is None:
            return SimpleVocabulary([])

        request = aq_get(ttool, 'REQUEST', None)
        items = [(translate(ttool[t].Title(), context=request), t)
                 for t in ptool.getUserFriendlyTypes()]
        items.sort()
        items = [SimpleTerm(i[1], i[1], i[0]) for i in items]
        return SimpleVocabulary(items)

UserFriendlyTypesVocabularyFactory = UserFriendlyTypesVocabulary()


BAD_TYPES = ("ATBooleanCriterion", "ATDateCriteria", "ATDateRangeCriterion",
             "ATListCriterion", "ATPortalTypeCriterion", "ATReferenceCriterion",
             "ATSelectionCriterion", "ATSimpleIntCriterion", "Plone Site",
             "ATSimpleStringCriterion", "ATSortCriterion", "TempFolder",
             "ATCurrentAuthorCriterion", "ATPathCriterion",
             "ATRelativePathCriterion", )


class ReallyUserFriendlyTypesVocabulary(object):
    """Vocabulary factory for really user friendly portal types.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyType
      >>> from plone.app.vocabularies.tests.base import DummyTypeTool

      >>> name = 'plone.app.vocabularies.ReallyUserFriendlyTypes'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> tool = DummyTypeTool()
      >>> tool['ATBooleanCriterion'] = DummyType('Boolean Criterion')
      >>> context.portal_types = tool

      >>> types = util(context)
      >>> types
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(types.by_token)
      2

      >>> doc = types.by_token['Document']
      >>> doc.title, doc.token, doc.value
      (u'Page', 'Document', 'Document')
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        ttool = getToolByName(site, 'portal_types', None)
        if ttool is None:
            return SimpleVocabulary([])

        request = aq_get(ttool, 'REQUEST', None)
        items = [(translate(ttool[t].Title(), context=request), t)
                 for t in ttool.listContentTypes()
                 if t not in BAD_TYPES]
        items.sort()
        items = [SimpleTerm(i[1], i[1], i[0]) for i in items]
        return SimpleVocabulary(items)

ReallyUserFriendlyTypesVocabularyFactory = ReallyUserFriendlyTypesVocabulary()
