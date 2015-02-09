
# Get the year and month that the calendar should display.

from Products.CMFCore.utils import getToolByName

caltool = getToolByName(script, 'portal_calendar')
current = DateTime()
session = None

# First priority goes to the data in the request
year = context.REQUEST.get('year', None)
month = context.REQUEST.get('month', None)

# Next get the data from the SESSION
if caltool.getUseSession():
    session = context.REQUEST.get('SESSION', None)
    if session:
        if not year:
            year = session.get('calendar_year', None)
        if not month:
            month = session.get('calendar_month', None)

# Last resort to today
if not year:
    year = current.year()
if not month:
    month = current.month()

# Then store the results in the session for next time
if session:
    session.set('calendar_year', year)
    session.set('calendar_month', month)

# Finally return the results
return (year, month)
