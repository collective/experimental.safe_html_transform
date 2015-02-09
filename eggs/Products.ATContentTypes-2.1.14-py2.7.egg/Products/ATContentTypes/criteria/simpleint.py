from zope.interface import implements

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import IntegerField
from Products.Archetypes.atapi import IntegerWidget
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

DirectionOperations = DisplayList((
    ('', _(u'Equal to')),
    ('min', _(u'Greater than')),
    ('max', _(u'Less than')),
    ('min:max', _(u'Between')),
    ))

ATSimpleIntCriterionSchema = ATBaseCriterionSchema + Schema((
    IntegerField('value',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Value",
                mutator="setValue",
                default=None,
                widget=IntegerWidget(
                    label=_(u'label_int_criteria_value', default=u'Value'),
                    description=_(u'help_int_criteria_value',
                                  default=u'An integer number.')
                    ),
                ),
    IntegerField('value2',
                required=0,
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Value2",
                mutator="setValue2",
                default=None,
                widget=IntegerWidget(
                    label=_(u'label_int_criteria_value2', default=u'Second Value'),
                    description=_(u'help_int_criteria_value2',
                                  default=u'An integer number used as the maximum value if the between direction is selected.')
                    ),
                ),
    StringField('direction',
                required=0,
                mode="rw",
                write_permission=ChangeTopics,
                default='',
                vocabulary=DirectionOperations,
                enforceVocabulary=1,
                widget=SelectionWidget(
                    label=_(u'label_int_criteria_direction', default=u'Direction'),
                    description=_(u'help_int_criteria_direction',
                                  default=u'Specify whether you want to find values lesser than, greater than, equal to, or between the chosen value(s).')
                    ),
                ),
    ))


class ATSimpleIntCriterion(ATBaseCriterion):
    """A simple int criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATSimpleIntCriterionSchema
    meta_type = 'ATSimpleIntCriterion'
    archetype_name = 'Simple Int Criterion'
    shortDesc = 'Integer value or range'

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []
        val = self.Value()
        direction = self.getDirection()
        if val or val == 0:
            if direction == 'min:max':
                val = tuple([int(val), int(self.Value2())])
            else:
                val = int(val)
            if direction:
                result.append((self.Field(), {'query': val, 'range': direction}))
            else:
                result.append((self.Field(), {'query': val}))

        return tuple(result)

    security.declareProtected(View, 'post_validate')
    def post_validate(self, REQUEST, errors):
        """Check that Value2 is set if range is set to min:max"""
        direction = REQUEST.get('direction', self.getDirection())
        val2 = REQUEST.get('value2', self.Value2())
        if direction == 'min:max' and not val2 and not val2 == 0:
            errors['value2'] = 'You must enter a second value to do a "Between" search.'
        errors['value2'] = 'You must enter a second value to do a "Between" search.'
        return errors

registerCriterion(ATSimpleIntCriterion, LIST_INDICES)
