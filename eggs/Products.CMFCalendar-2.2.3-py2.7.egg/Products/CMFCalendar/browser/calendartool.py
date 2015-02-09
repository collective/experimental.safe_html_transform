##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser views for the portal calendar.

$Id: calendartool.py 110663 2010-04-08 15:59:45Z tseaver $
"""

from DateTime.DateTime import DateTime

from Products.CMFDefault.browser.utils import decode
from Products.CMFDefault.browser.utils import memoize
from Products.CMFDefault.browser.utils import ViewBase


class CalendarView(ViewBase):

    """ Helper class for calendar-related templates
    """

    # helpers

    def _getStartAsString(self, event_brain):
        """ Retrieve formatted start string
        """
        day = self.viewDay()
        event_start = event_brain.getObject().start()
        first_date = DateTime(day.Date()+" 00:00:00")

        if event_start < first_date:
            return event_start.aCommon()[:12]
        else:
            return event_start.TimeMinutes()

    def _getEndAsString(self, event_brain):
        """ Retrieve formatted end string
        """
        day = self.viewDay()
        event_end = event_brain.getObject().end()
        last_date = DateTime(day.Date()+" 23:59:59")

        if event_end > last_date:
            return event_end.aCommon()[:12]
        else:
            return event_end.TimeMinutes()

    @memoize
    def viewDay(self):
        """ Return a DateTime for a passed-in date or today
        """
        date = self.request.get('date', None) or DateTime().aCommon()[:12]

        return DateTime(date)

    # interface

    @memoize
    def formattedDate(self):
        """ Return a simple formatted date string
        """
        return self.viewDay().aCommon()[:12]

    @memoize
    def previousDayURL(self):
        """ URL to the previous day's view
        """
        day = self.viewDay()
        view_url = self._getViewURL()

        return '%s?date=%s' % (view_url, (day-1).Date())

    @memoize
    def nextDayURL(self):
        """ URL to the next day's view
        """
        day = self.viewDay()
        view_url = self._getViewURL()

        return '%s?date=%s' % (view_url, (day+1).Date())

    @memoize
    @decode
    def listItemInfos(self):
        """ List item infos for all event catalog records for a specific day.
        """
        caltool = self._getTool('portal_calendar')
        thisDay = self.viewDay()

        items = [ {'title': item.Title,
                   'url': item.getURL(),
                   'start': self._getStartAsString(item),
                   'stop': self._getEndAsString(item)}
                  for item in caltool.getEventsForThisDay(thisDay) ]

        return tuple(items)


class CalendarBoxView(ViewBase):

    # calendarBox widget helpers

    @memoize
    def getMonthAndYear(self):
        """ Retrieve month/year tuple
        """
        caltool = self._getTool('portal_calendar')
        current = DateTime()
        session = None

        # First priority goes to the data in the request
        year = self.request.get('year', None)
        month = self.request.get('month', None)

        # Next get the data from the SESSION
        if caltool.getUseSession():
            session = self.request.get('SESSION', None)
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

    def getNextMonthLink(self, base_url, month, year):
        """ Return URL for the next month link
        """
        caltool = self._getTool('portal_calendar')
        nextMonthTime = caltool.getNextMonth(month, year)

        x = '%s?month:int=%d&year:int=%d' % ( base_url
                                            , nextMonthTime.month()
                                            , nextMonthTime.year()
                                            )

        return x

    def getPreviousMonthLink(self, base_url, month, year):
        """ Return URL for the previous month link
        """
        caltool = self._getTool('portal_calendar')
        prevMonthTime = caltool.getPreviousMonth(month, year)

        x = '%s?month:int=%d&year:int=%d' % ( base_url
                                            , prevMonthTime.month()
                                            , prevMonthTime.year()
                                            )

        return x

    def getDaysClass(self, day, month, year, event=None):
        """ Determine the CSS class to use for the given day
        """
        current = DateTime()

        if ( current.year()==year and
             current.month()==month and
             current.day()==int(day) ):
            if event:
                return 'todayevent'
            else:
                return 'todaynoevent'

        if event:
            return 'event'
        else:
            return ''
