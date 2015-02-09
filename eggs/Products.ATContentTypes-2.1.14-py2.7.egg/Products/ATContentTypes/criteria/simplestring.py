from zope.interface import implements

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import StringWidget

from Products.ATContentTypes.criteria import registerCriterion, \
    STRING_INDICES
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion

from Products.ATContentTypes.permission import ChangeTopics
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema

from Products.ATContentTypes import ATCTMessageFactory as _

ATSimpleStringCriterionSchema = ATBaseCriterionSchema + Schema((
    StringField('value',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Value",
                mutator="setValue",
                default="",
                widget=StringWidget(
                    label=_(u'label_string_criteria_value', default=u'Value'),
                    description=_(u'help_string_criteria_value',
                                  default=u'A string value.'))
                ),
    ))


class ATSimpleStringCriterion(ATBaseCriterion):
    """A simple string criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATSimpleStringCriterionSchema
    meta_type = 'ATSimpleStringCriterion'
    archetype_name = 'Simple String Criterion'
    shortDesc = 'Text'

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []

        if self.Value() is not '':
            result.append((self.Field(), self.Value()))

        return tuple(result)

registerCriterion(ATSimpleStringCriterion, STRING_INDICES + ('UUIDIndex', ))
