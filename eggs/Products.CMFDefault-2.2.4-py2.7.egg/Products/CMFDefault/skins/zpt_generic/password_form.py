##parameters=change='', cancel=''
##
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.utils import decode
from Products.CMFDefault.utils import Message as _

atool = getToolByName(script, 'portal_actions')
mtool = getToolByName(script, 'portal_membership')
ptool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IPropertiesTool')
utool = getToolByName(script, 'portal_url')
member = mtool.getAuthenticatedMember()
portal_url = utool()

form = context.REQUEST.form
if change and \
        context.change_password(**form) and \
        context.setRedirect(atool, 'user/preferences'):
    return
elif cancel and \
        context.setRedirect(atool, 'user/preferences'):
    return


options = {}

is_first_login = (member.getProperty('last_login_time') == DateTime('1999/01/01'))
options['is_first_login'] = is_first_login
if is_first_login:
    options['title'] = _(u'Welcome!')
    options['portal_title'] = ptool.getProperty('title')
else:
    options['title'] = _(u'Change your Password')
options['member_id'] = member.getId()
options['domains'] = ' '.join(member.getDomains())
buttons = []
target = '%s/password_form' % portal_url
buttons.append( {'name': 'change', 'value': _(u'Change')} )
if not is_first_login:
    buttons.append( {'name': 'cancel', 'value': _(u'Cancel')} )
options['form'] = { 'action': target,
                    'listButtonInfos': tuple(buttons) }

return context.password_form_template(**decode(options, script))
