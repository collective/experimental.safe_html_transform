from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.site.hooks import getSite

from Products.CMFCore.utils import getToolByName

_ = MessageFactory('plone')


class SkinsVocabulary(object):
    """Vocabulary factory for skins.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool

      >>> name = 'plone.app.vocabularies.Skins'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> len(util(context))
      0

      >>> tool = DummyTool('portal_skins')
      >>> def getSkinSelections():
      ...     return ('Plone Default', 'Plone Kitty')
      >>> tool.getSkinSelections = getSkinSelections
      >>> context.portal_skins = tool

      >>> skins = util(context)
      >>> skins
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(skins.by_token)
      2

      >>> term = skins.by_token['Plone Kitty']
      >>> term.title, term.token, term.value
      ('Plone Kitty', 'Plone Kitty', 'Plone Kitty')

      Plone Default is a special case that gets a different title
      for clarification.
      >>> term = skins.by_token['Plone Default']
      >>> term.title, term.token, term.value
      (u'(Unstyled)', 'Plone Default', 'Plone Default')
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        site = getSite()
        stool = getToolByName(site, 'portal_skins', None)
        if stool is not None:
            items = list(stool.getSkinSelections())
            items.sort()
            if 'Plone Default' in items:
                terms = [SimpleTerm('Plone Default', 'Plone Default', _(u'(Unstyled)'))]
                items.remove('Plone Default')
            terms += [SimpleTerm(i, i, i) for i in items]
        return SimpleVocabulary(terms)

SkinsVocabularyFactory = SkinsVocabulary()
