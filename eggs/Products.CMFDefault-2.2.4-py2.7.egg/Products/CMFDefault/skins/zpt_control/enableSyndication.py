## Script (Python) "enableSyndication"
##title=Enable Syndication for a resource
##parameters=

if context.portal_syndication.isSiteSyndicationAllowed():
    context.portal_syndication.enableSyndication(context)
    msg = 'Syndication+Enabled'
else:
    msg = 'Syndication+Not+Allowed'

target = '%s/synPropertiesForm' % context.absolute_url()
qs = 'portal_status_message=%s' % msg

return context.REQUEST.RESPONSE.redirect('%s?%s' % (target, qs))
