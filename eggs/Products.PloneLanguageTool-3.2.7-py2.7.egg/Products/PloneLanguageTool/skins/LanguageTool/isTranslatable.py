## Script (Python) "isTranslatable"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
try :
    return context.portal_url.getPortalObject().portal_languages.isTranslatable(context)
except:
    return 0
