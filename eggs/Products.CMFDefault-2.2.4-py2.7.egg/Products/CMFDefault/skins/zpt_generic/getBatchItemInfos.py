## Script (Python) "getBatchItemInfos"
##parameters=batch_obj
##title=
##
items = []
for item in batch_obj:
    item_description = item.Description()
    item_title = item.Title()
    item_type = remote_type = item.Type()
    if item_type == 'Favorite':
        try:
            item = item.getObject()
            item_description = item_description or item.Description()
            item_title = item_title or item.Title()
            remote_type = item.Type()
        except KeyError:
            pass
    is_file = remote_type in ('File', 'Image')
    is_link = remote_type == 'Link'
    items.append({'description': item_description,
                  'format': is_file and item.Format() or '',
                  'icon': item.getIconURL(),
                  'size': is_file and ('%0.0f kb' %
                                       (item.get_size() / 1024.0)) or '',
                  'title': item_title,
                  'type': item_type,
                  'url': is_link and item.getRemoteUrl() or
                         item.absolute_url()})
return tuple(items)
