## Script (Python) "validate_set_sort"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##
from Products.ATContentTypes import ATCTMessageFactory as _

indexId=context.REQUEST.get('field')
if indexId == 'no_sort':
    return state.set(status='success')
supported = context.validateAddCriterion(indexId, 'ATSortCriterion')
if not supported:
    msg = _(u'Sort order on field '
             '${field} not set, it cannot be used for ordering.',
             mapping={'field' : indexId})
    context.plone_utils.addPortalMessage(msg, 'error')
    return state.set(status='failure')
else:
    return state.set(status='success')
