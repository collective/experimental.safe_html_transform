# -*- coding:utf-8 -*-
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from Products.CMFCore.utils import getToolByName


class ActionCategoriesVocabulary(object):
    """Provides an actions categories vocabulary"""

    implements(IVocabularyFactory)

    def __call__(self, context):
        portal_actions = getToolByName(context, 'portal_actions')

        # Building the list of action categories
        try:
            categories = portal_actions.listFilteredActionsFor(context).keys()
        except:
            portal = context.portal_url.getPortalObject()
            categories = portal.portal_actions.objectIds()
        categories.sort()
        return SimpleVocabulary([SimpleTerm(cat, title=cat) for cat in categories])


ActionCategoriesVocabularyFactory = ActionCategoriesVocabulary()
