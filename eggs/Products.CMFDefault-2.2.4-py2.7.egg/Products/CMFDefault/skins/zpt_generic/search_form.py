##parameters=search=''
##
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.permissions import ReviewPortalContent
from Products.CMFDefault.utils import decode
from Products.CMFDefault.utils import Message as _

ctool = getToolByName(script, 'portal_catalog')
mtool = getToolByName(script, 'portal_membership')
ttool = getToolByName(script, 'portal_types')
utool = getToolByName(script, 'portal_url')
portal_url = utool()


options = {}
options['title'] = context.Title()

is_review_allowed = mtool.checkPermission(ReviewPortalContent, context)
options['is_review_allowed'] = is_review_allowed
options['listAvailableSubjects'] = ctool.uniqueValuesFor('Subject')

created = []
today = context.ZopeTime().earliestTime()
created.append({'value': '1970/01/01 00:00:01 GMT', 'title': _(u'Ever')})
if not mtool.isAnonymousUser():
    created.append({'value': mtool.getAuthenticatedMember().last_login_time,
                    'title': _(u'Last login')})
created.append({'value': (today-1).Date(), 'title': _(u'Yesterday')})
created.append({'value': (today-7).Date(), 'title': _(u'Last week')})
created.append({'value': (today-31).Date(), 'title': _(u'Last month')})
options['listCreatedInfos'] = tuple(created)

options['listTypeInfos'] = ttool.listTypeInfo()

buttons = []
target = '%s/search' % portal_url
buttons.append( {'name': 'search', 'value': _(u'Search')} )
options['form'] = { 'action': target,
                    'listButtonInfos': tuple(buttons) }

return context.search_form_template(**decode(options, script))
