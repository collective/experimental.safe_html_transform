## Controller Python Script "criterion_add"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=field, criterion_type
##title=Criterion Add

from Products.ATContentTypes import ATCTMessageFactory as _
from Products.Archetypes.utils import transaction_note

context.addCriterion(field, criterion_type)

msg = _(u'Added criterion ${criterion} for field ${field}.',
        mapping={'criterion' : criterion_type, 'field' : field})
transaction_note(msg)
context.plone_utils.addPortalMessage(msg)

return state
