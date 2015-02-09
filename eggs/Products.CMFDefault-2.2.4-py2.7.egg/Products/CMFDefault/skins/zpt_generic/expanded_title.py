## Script (Python) "expanded_title"
##parameters=
##title=Build title which includes site title
##
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.utils import decode

utool = getToolByName(script, 'portal_url')

site_title = utool.getPortalObject().Title()
page_title = context.Title()

if page_title != site_title:
   page_title = site_title + ": " + page_title

return decode(page_title, script)
