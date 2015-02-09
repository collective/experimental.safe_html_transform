from zope.interface import implements

from DateTime import DateTime
from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import IntegerField
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import DisplayList
from Products.Archetypes.atapi import IntDisplayList

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import DATE_INDICES
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics

from Products.ATContentTypes import ATCTMessageFactory as _

DateOptions = IntDisplayList((
    (0, _(u'Now')),
    (1, _(u'1 Day')),
    (2, _(u'2 Days')),
    (5, _(u'5 Days')),
    (7, _(u'1 Week')),
    (14, _(u'2 Weeks')),
    (31, _(u'1 Month')),
    (31 * 3, _(u'3 Months')),
    (31 * 6, _(u'6 Months')),
    (365, _(u'1 Year')),
    (365 * 2, _(u'2 Years')),
    ))

CompareOperations = DisplayList((
    ('more', _(u'More than')),
    ('less', _(u'Less than')),
    ('within_day', _(u'On the day')),
    ))

RangeOperations = DisplayList((
    ('-', _(u'in the past')),
    ('+', _(u'in the future')),
    ))

ATDateCriteriaSchema = ATBaseCriterionSchema + Schema((
    IntegerField('value',
                required=1,
                mode="rw",
                accessor="Value",
                mutator="setValue",
                write_permission=ChangeTopics,
                default=None,
                vocabulary=DateOptions,
                widget=SelectionWidget(
                    label=_(u'label_date_criteria_value', default=u'Which day'),
                    description=_(u'help_date_criteria_value',
                                  default=u'Select the date criteria value.')
                    ),
                ),
    StringField('dateRange',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                default=None,
                vocabulary=RangeOperations,
                enforceVocabulary=1,
                widget=SelectionWidget(
                    label=_(u'label_date_criteria_range',
                            default=u'In the past or future'),
                    description=_(u'help_date_criteria_range',
                                  default=u"Select the date criteria range. Ignore this if you selected 'Now' above."),
                    format="select"),
                ),
    StringField('operation',
                required=1,
                mode="rw",
                default=None,
                write_permission=ChangeTopics,
                vocabulary=CompareOperations,
                enforceVocabulary=1,
                widget=SelectionWidget(
                    label=_(u'label_date_criteria_operation', default=u'More or less'),
                    description=_(u'help_date_criteria_operation',
                                  default=u'Select the date criteria operation.'),
                    format="select"),
                ),
    ))


class ATDateCriteria(ATBaseCriterion):
    """A relative date criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATDateCriteriaSchema
    meta_type = 'ATFriendlyDateCriteria'
    archetype_name = 'Friendly Date Criteria'
    shortDesc = 'Relative date'

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        """Return a sequence of items to be used to build the catalog query.
        """
        if self.value is not None:
            field = self.Field()
            value = self.Value()

            # Negate the value for 'old' days
            if self.getDateRange() == '-':
                value = -value

            date = DateTime() + value
            current_date = DateTime()

            operation = self.getOperation()
            if operation == 'within_day':
                date_range = (date.earliestTime(), date.latestTime())
                return ((field, {'query': date_range, 'range': 'min:max'}),)
            elif operation == 'more':
                if value != 0:
                    range_op = (self.getDateRange() == '-' and 'max') or 'min'
                    return ((field, {'query': date.earliestTime(), 'range': range_op}),)
                else:
                    return ((field, {'query': date, 'range': 'min'}),)
            elif operation == 'less':
                if value != 0:
                    date_range = (self.getDateRange() == '-' and
                                  (date.earliestTime(), current_date)
                                  ) or (current_date, date.latestTime())
                    return ((field, {'query': date_range, 'range': 'min:max'}),)
                else:
                    return ((field, {'query': date, 'range': 'max'}),)
        else:
            return ()

registerCriterion(ATDateCriteria, DATE_INDICES)
