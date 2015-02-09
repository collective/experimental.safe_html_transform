## Script (Python) "getValidIndexes"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=index
##title=Determine whether to show an id in an edit form

return context.allowedCriteriaForField(index, display_list=True)
