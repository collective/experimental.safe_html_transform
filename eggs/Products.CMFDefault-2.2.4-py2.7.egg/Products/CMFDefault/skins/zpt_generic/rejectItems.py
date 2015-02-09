## Script (Python) "rejectItems"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=items, comment=''
##title=
##
from Products.CMFCore.utils import getToolByName

wtool = getToolByName(script, 'portal_workflow')
for path in items:
    object = context.restrictedTraverse( path )
    wtool.doActionFor( object, 'reject', comment=comment )

context.REQUEST[ 'RESPONSE' ].redirect( '%s/review?%s'
                   % ( context.portal_url()
                     , 'portal_status_message=Items+rejected.'
                     ) )
