##parameters=base_url, month, year

prevMonthTime = container.portal_calendar.getPreviousMonth(month, year)

# Takes a base url and returns a link to the previous month
x = '%s?month:int=%d&year:int=%d' % (
                                     base_url,
                                     prevMonthTime.month(),
                                     prevMonthTime.year()
                                     )

return x