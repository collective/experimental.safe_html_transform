## Script (Python) "unittestGetTitleOf"
##title=Helper method for function tests
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=

return "%s,%s,%s,%s" % (context.title_or_id(), context.aq_parent.title_or_id(),\
 context.aq_inner.title_or_id(), context.aq_inner.aq_parent.title_or_id())
