##parameters=change_type
##title=Set local roles
##
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.utils import Message as _

mtool = getToolByName(script, 'portal_membership')

if change_type == 'add':
    mtool.setLocalRoles(obj=context,
                        member_ids=context.REQUEST.get('member_ids', ()),
                        member_role=context.REQUEST.get('member_role', ''),
                        REQUEST=context.REQUEST)
else:
    mtool.deleteLocalRoles(obj=context,
                           member_ids=context.REQUEST.get('member_ids', ()),
                           REQUEST=context.REQUEST)

context.setStatus(True, _(u'Local Roles changed.'))
context.setRedirect(context, 'object/localroles')
