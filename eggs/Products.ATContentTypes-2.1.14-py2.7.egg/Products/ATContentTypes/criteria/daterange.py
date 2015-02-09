from zope.interface import implements

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import DateTimeField
from Products.Archetypes.atapi import CalendarWidget

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import DATE_INDICES
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics

from Products.ATContentTypes import ATCTMessageFactory as _

RELEVANT_INDICES = list(DATE_INDICES)
RELEVANT_INDICES.remove('DateRangeIndex')
RELEVANT_INDICES = tuple(RELEVANT_INDICES)

ATDateRangeCriterionSchema = ATBaseCriterionSchema + Schema((
    DateTimeField('start',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                default=None,
                widget=CalendarWidget(
                    label=_(u'label_date_range_criteria_start', default=u'Start Date'),
                    description=_(u'help_date_range_criteria_start',
                                  default=u'The beginning of the date range to search')
                    ),
                ),
    DateTimeField('end',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                default=None,
                widget=CalendarWidget(
                    label=_(u'label_date_range_criteria_end', default=u'End Date'),
                    description=_(u'help_date_range_criteria_end',
                                  default=u'The ending of the date range to search.')

                    ),
                ),
    ))


class ATDateRangeCriterion(ATBaseCriterion):
    """A date range criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATDateRangeCriterionSchema
    meta_type = 'ATDateRangeCriterion'
    archetype_name = 'Date Range Criterion'
    shortDesc = 'Date range'

    security.declareProtected(View, 'Value')
    def Value(self):
        return (self.getStart(), self.getEnd())

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []

        field = self.Field()
        value = self.Value()

        return ((field, {'query': value, 'range': 'min:max'}),)

registerCriterion(ATDateRangeCriterion, RELEVANT_INDICES)
