from zope.interface import implements

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import LinesWidget
from Products.Archetypes.atapi import DisplayList

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import LIST_INDICES
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics

from Products.ATContentTypes import ATCTMessageFactory as _

CompareOperators = DisplayList((
    ('and', _(u'and')),
    ('or', _(u'or')),
    ))

ATListCriterionSchema = ATBaseCriterionSchema + Schema((
    LinesField('value',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Value",
                mutator="setValue",
                default=[],
                widget=LinesWidget(
                    label=_(u'label_list_criteria_value', default=u'Values'),
                    description=_(u'help_list_criteria_value',
                                  default=u'Values, each on its own line.')
                    ),
                ),
    StringField('operator',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                default='or',
                vocabulary=CompareOperators,
                widget=SelectionWidget(
                    label=_(u'label_list_criteria_operator',
                            default=u'operator name'),
                    description=_(u'help_list_criteria_operator',
                                  default=u'Operator used to join the tests on each value.')
                    ),
                ),
    ))


class ATListCriterion(ATBaseCriterion):
    """A list criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATListCriterionSchema
    meta_type = 'ATListCriterion'
    archetype_name = 'List Criterion'
    shortDesc = 'List of values'

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        # filter out empty strings
        result = []

        value = tuple([value for value in self.Value() if value])
        if not value:
            return ()
        result.append((self.Field(), {'query': value, 'operator': self.getOperator()}),)

        return tuple(result)

registerCriterion(ATListCriterion, LIST_INDICES)
