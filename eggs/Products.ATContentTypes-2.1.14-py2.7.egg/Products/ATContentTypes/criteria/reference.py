from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from AccessControl import ClassSecurityInfo

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import REFERENCE_INDICES
from Products.ATContentTypes.criteria.selection import ATSelectionCriterion
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.Archetypes.atapi import DisplayList

ATReferenceCriterionSchema = ATSelectionCriterion.schema


class ATReferenceCriterion(ATSelectionCriterion):
    """A reference criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    meta_type = 'ATReferenceCriterion'
    archetype_name = 'Reference Criterion'
    shortDesc = 'Select referenced content'

    def getCurrentValues(self):
        catalog = getToolByName(self, 'portal_catalog')
        uid_cat = getToolByName(self, 'uid_catalog')
        putils = getToolByName(self, 'plone_utils')
        options = catalog.uniqueValuesFor(self.Field())

        # If the uid catalog has a Language index restrict the query by it.
        # We should only shows references to items in the same or the neutral
        # language.
        query = dict(UID=options, sort_on='Title')
        if 'Language' in uid_cat.indexes():
            query['Language'] = [self.Language(), '']

        brains = uid_cat(**query)
        display = [((putils.pretty_title_or_id(b)).lower(), b.UID, b.Title or b.id) for b in brains]
        display.sort()
        display_list = DisplayList([(d[1], d[2]) for d in display])

        return display_list

registerCriterion(ATReferenceCriterion, REFERENCE_INDICES)
