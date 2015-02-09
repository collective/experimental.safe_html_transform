from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import IdWidget
from Products.Archetypes.atapi import StringWidget
from Products.ATContentTypes.permission import ChangeTopics

from Products.ATContentTypes import ATCTMessageFactory as _

###
# AT Base Criterion
###

ATBaseCriterionSchema = Schema((
    StringField('id',
                required=1,
                mode="r",
                default=None,
                write_permission=ChangeTopics,
                widget=IdWidget(
                    label=_(u'label_short_name', default=u'Short Name'),
                    description=_(u'help_shortname',
                                  default=u"Should not contain spaces, underscores or mixed case. "
                                           "Short Name is part of the item's web address."),
                    visible={'view': 'invisible'}
                    ),
                ),
    StringField('field',
                required=1,
                mode="r",
                accessor="Field",
                write_permission=ChangeTopics,
                default=None,
                widget=StringWidget(
                    label=_(u'label_criteria_field_name', default=u'Field name'),
                    description=_(u'help_shortname',
                                  default=u"Should not contain spaces, underscores or mixed case. "
                                           "Short Name is part of the item's web address.")
                    ),
                ),
    ))
