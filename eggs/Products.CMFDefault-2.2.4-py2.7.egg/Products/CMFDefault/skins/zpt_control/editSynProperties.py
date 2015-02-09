## Script (Python) "editSynProperties"
##title=Enable Syndication for a resource
##parameters=
REQUEST=context.REQUEST
pSyn = context.portal_syndication
pSyn.editSyInformationProperties(context, REQUEST['updatePeriod'], REQUEST['updateFrequency'], REQUEST['updateBase'], REQUEST['max_items'], REQUEST)
return REQUEST.RESPONSE.redirect(context.absolute_url() + '/synPropertiesForm?portal_status_message=Syndication+Properties+Updated.')
