##parameters=
##
from ZTUtils import Batch
from ZTUtils import LazyFilter
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.CMFDefault.utils import decode

stool = getUtilityByInterfaceName('Products.CMFCore.interfaces.ISyndicationTool')


if not stool.isSyndicationAllowed(context):
    context.REQUEST.RESPONSE.redirect(context.absolute_url() +
             '/rssDisabled?portal_status_message=Syndication+is+Disabled')
    return


options = {}

options['channel_info'] = { 'base': stool.getHTML4UpdateBase(context),
                            'description': context.Description(),
                            'frequency': stool.getUpdateFrequency(context),
                            'period': stool.getUpdatePeriod(context),
                            'title': context.Title(),
                            'url': context.absolute_url() }

key, reverse = context.getDefaultSorting()
items = stool.getSyndicatableContent(context)
items = sequence.sort( items, ((key, 'cmp', reverse and 'desc' or 'asc'),) )
items = LazyFilter(items, skip='View')
b_size = stool.getMaxItems(context)
batch_obj = Batch(items, b_size, 0, orphan=0)
items = []
for item in batch_obj:
    items.append( { 'date': item.modified().HTML4(),
                    'description': item.Description(),
                    'listCreators': item.listCreators(),
                    'listSubjects': item.Subject(),
                    'publisher': item.Publisher(),
                    'rights': item.Rights(),
                    'title': item.Title(),
                    'url': item.absolute_url() } )
options['listItemInfos'] = tuple(items)

return context.RSS_template(**decode(options, script))
