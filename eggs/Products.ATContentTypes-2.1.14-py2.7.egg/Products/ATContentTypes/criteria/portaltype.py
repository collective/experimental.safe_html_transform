from zope.component import queryUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory

from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import DisplayList
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import FIELD_INDICES
from Products.ATContentTypes.criteria.selection import ATSelectionCriterion
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion

from Products.ATContentTypes import ATCTMessageFactory as _

ATPortalTypeCriterionSchema = ATSelectionCriterion.schema.copy()
# and/or operator makes no sense for type selection, as no item can ever be
# two types at the same time fulfilling an AND condition
ATPortalTypeCriterionSchema.delField("operator")

val_widget = ATPortalTypeCriterionSchema['value'].widget
val_widget.description = _(u'help_portal_type_criteria_value',
                           default=u'One of the available content types.')
ATPortalTypeCriterionSchema['value'].widget = val_widget

VOCAB_ID = u'plone.app.vocabularies.ReallyUserFriendlyTypes'


class ATPortalTypeCriterion(ATSelectionCriterion):
    """A portal_types criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATPortalTypeCriterionSchema
    meta_type = 'ATPortalTypeCriterion'
    archetype_name = 'Portal Types Criterion'
    shortDesc = 'Select content types'

    security.declareProtected(View, 'getCurrentValues')
    def getCurrentValues(self):
        """Return enabled portal types"""
        vocab = queryUtility(IVocabularyFactory, name=VOCAB_ID)(self)
        portal_types = getToolByName(self, 'portal_types', None)
        result = []
        # the vocabulary returns the values sorted by their translated title
        for term in vocab._terms:
            value = term.value  # portal_type
            title = term.title  # already translated title
            if self.Field() == 'Type':
                # Switch the value from portal_type to the Title msgid
                # since that is stored in the Type-index in portal_catalog
                # TODO: we should really use the portal_type index here and
                # remove the Type index
                value = unicode(portal_types[value].Title())
            result.append((value, title))

        return DisplayList(result)

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []
        if self.Value() is not '':
            result.append((self.Field(), self.Value()))

        return tuple(result)

registerCriterion(ATPortalTypeCriterion, FIELD_INDICES)
