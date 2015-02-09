##parameters=
##
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.utils import decode

caltool = getToolByName(script, 'portal_calendar')

options = {}
base_url = script.absolute_url()
thisDay = DateTime(context.REQUEST.get('date', DateTime().aCommon()[:12]))
options['previous_url'] = '%s?date=%s' % (base_url, (thisDay-1).Date())
options['date'] = thisDay.aCommon()[:12]
options['next_url'] =  '%s?date=%s' % (base_url, (thisDay+1).Date())

items = [ {'title': item.Title,
           'url': item.getURL(),
           'start': context.getStartAsString(thisDay, item),
           'stop': context.getEndAsString(thisDay, item)}
          for item in caltool.getEventsForThisDay(thisDay) ]

options['listItemInfos'] = tuple(items)

return context.calendar_day_view_template(**decode(options, script))
