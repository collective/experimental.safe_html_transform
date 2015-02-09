## Controller Python Script "criterion_remove"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=criterion_ids=[]
##title=Criterion Remove

from Products.ATContentTypes import ATCTMessageFactory as _
from Products.Archetypes.utils import transaction_note

remove=[]

criteria = context.listCriteria()
for crit in criteria:
    id  = crit.getId()

    if id in criterion_ids:
        remove.append(id) 
        
context.deleteCriterion(remove)

msg = _(u'Removed criteria ${criteria}.',
        mapping={'criteria' : u','.join(remove)})
transaction_note(msg)
context.plone_utils.addPortalMessage(msg)

return state
