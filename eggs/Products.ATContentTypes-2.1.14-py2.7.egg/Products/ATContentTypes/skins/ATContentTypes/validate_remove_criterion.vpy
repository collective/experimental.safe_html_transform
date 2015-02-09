## Script (Python) "validate_remove_criterion"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##
from Products.ATContentTypes import ATCTMessageFactory as _
 
criterion_ids=context.REQUEST.get('criterion_ids')
if not criterion_ids:
    msg = _(u'You must first select a criterion to remove.')
    context.plone_utils.addPortalMessage(msg, 'error')
    return state.set(status='failure')
else:
    return state.set(status='success')
