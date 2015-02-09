from zope.interface import implements

from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import MultiSelectionWidget
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import DisplayList

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import LIST_INDICES
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema

from Products.ATContentTypes import ATCTMessageFactory as _

CompareOperators = DisplayList((
    ('and', _(u'and')),
    ('or', _(u'or')),
    ))

ATSelectionCriterionSchema = ATBaseCriterionSchema + Schema((
    LinesField('value',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Value",
                mutator="setValue",
                default=[],
                vocabulary="getCurrentValues",
                widget=MultiSelectionWidget(
                    label=_(u'label_criteria_values', default=u'Values'),
                    description=_(u'help_criteria_values', default=u'Existing values.')
                    ),
                ),
    StringField('operator',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                default='or',
                vocabulary=CompareOperators,
                widget=SelectionWidget(
                    label=_(u'label_list_criteria_operator', default=u'operator name'),
                    description=_(u'help_list_criteria_operator',
                                  default=u'Operator used to join the tests on each value.')
                    ),
                ),
    ))


class ATSelectionCriterion(ATBaseCriterion):
    """A selection criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATSelectionCriterionSchema
    meta_type = 'ATSelectionCriterion'
    archetype_name = 'Selection Criterion'
    shortDesc = 'Select values from list'

    def getCurrentValues(self):
        catalog = getToolByName(self, 'portal_catalog')
        options = catalog.uniqueValuesFor(self.Field())
        # AT is currently broken, and does not accept ints as
        # DisplayList keys though it is supposed to (it should
        # probably accept Booleans as well) so we only accept strings
        # for now
        options = [(o.lower(), o) for o in options if isinstance(o, basestring)]
        options.sort()
        return [o[1] for o in options]

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        # filter out empty strings
        result = []

        value = tuple([value for value in self.Value() if value])
        if not value:
            return ()
        result.append((self.Field(), {'query': value, 'operator': self.getOperator()}),)

        return tuple(result)

registerCriterion(ATSelectionCriterion, LIST_INDICES)
