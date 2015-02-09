## Script (Python) "atctListAlbum"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=images=0, folders=0, subimages=0, others=0
##title=Helper method for photo album view
##
result = {}
is_topic = context.portal_type == 'Topic'

if images:
    if is_topic:
        result['images'] = context.queryCatalog(portal_type=('Image',),
                                                full_objects=True)
    else:
        result['images'] = context.getFolderContents({'portal_type': ('Image',)},
                                                     full_objects=True)

if folders:
    # We don't need the full objects for the folders
    if is_topic:
        result['folders'] = context.queryCatalog(portal_type='Folder')
    else:
        result['folders'] = context.getFolderContents({'portal_type': ('Folder',)})

if subimages:
    # Handle brains or objects
    if getattr(context, 'getPath', None) is not None:
        path = context.getPath()
    else:
        path = '/'.join(context.getPhysicalPath())
    # Explicitly set path to remove default depth
    if is_topic:
        result['subimages'] = context.queryCatalog(portal_type=('Image',),
                                                   path=path)
    else:
        result['subimages'] = context.getFolderContents({'portal_type': ('Image',),
                                                 'path': path})

if others:
    searchContentTypes = context.plone_utils.getUserFriendlyTypes()
    filtered = [p_type for p_type in searchContentTypes
                if p_type not in ('Image', 'Folder',)]
    if filtered:
        # We don't need the full objects for the folder_listing
        if is_topic:
            result['others'] = context.queryCatalog(portal_type=filtered)
        else:
            result['others'] = context.getFolderContents({'portal_type': filtered})
    else:
        result['others'] = ()

return result
