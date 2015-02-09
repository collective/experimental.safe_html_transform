## Controller Python Script "criterion_set_sort"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=field, reversed=0
##title=Criterion Set Sort

REQUEST=context.REQUEST
from Products.ATContentTypes import ATCTMessageFactory as _
from Products.Archetypes.utils import transaction_note

if field == 'no_sort':
    context.removeSortCriterion()
else:
    context.setSortCriterion(field, reversed)

msg = _(u'Sort order set on field ${field}.',
        mapping={'field':field})
transaction_note(msg)
context.plone_utils.addPortalMessage(msg)

return state
