## Script (Python) "disableSyndication"
##title=Disable Syndication for a resource
##parameters=

if context.portal_syndication.isSyndicationAllowed(context):
  context.portal_syndication.disableSyndication(context)
  return context.REQUEST.RESPONSE.redirect(context.absolute_url() + '/synPropertiesForm?portal_status_message=Syndication+Disabled')
else:
  return context.REQUEST.RESPONSE.redirect(context.absolute_url() + '/synPropertiesForm?portal_status_message=Syndication+Not+Allowed')
