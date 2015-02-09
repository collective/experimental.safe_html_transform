from zope.interface import implements

from Missing import MV

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import BooleanWidget

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import FIELD_INDICES
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics

from Products.ATContentTypes import ATCTMessageFactory as _

ATBooleanCriterionSchema = ATBaseCriterionSchema + Schema((
    BooleanField('bool',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                default=None,
                widget=BooleanWidget(
                    label=_(u'label_boolean_criteria_bool', default=u'Value'),
                    description=_(u'help_boolean_criteria_bool',
                                  default=u'True or false')
                    ),
                ),
    ))


class ATBooleanCriterion(ATBaseCriterion):
    """A boolean criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATBooleanCriterionSchema
    meta_type = 'ATBooleanCriterion'
    archetype_name = 'Boolean Criterion'
    shortDesc = 'Boolean (True/False)'

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []
        if self.getBool():
            value = [1, True, '1', 'True']
        else:
            value = [0, '', False, '0', 'False', None, (), [], {}, MV]
        result.append((self.Field(), value))

        return tuple(result)

registerCriterion(ATBooleanCriterion, FIELD_INDICES + ('BooleanIndex', ))
