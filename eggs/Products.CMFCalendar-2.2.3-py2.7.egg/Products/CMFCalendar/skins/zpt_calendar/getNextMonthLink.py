##parameters=base_url, month, year

nextMonthTime = container.portal_calendar.getNextMonth(month, year)

# Takes a base url and returns a link to the previous month
x = '%s?month:int=%d&year:int=%d' % (
                                     base_url,
                                     nextMonthTime.month(),
                                     nextMonthTime.year()
                                     )

return x