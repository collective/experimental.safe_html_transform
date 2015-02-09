##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFCalendar portal_calendar tool.

$Id: CalendarTool.py 110663 2010-04-08 15:59:45Z tseaver $
"""

import calendar

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from DateTime.DateTime import DateTime
from OFS.SimpleItem import SimpleItem
from zope.interface import implements
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCalendar.interfaces import ICalendarTool
from Products.CMFCalendar.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import UniqueObject

def sort_by_date(x, y):
    """ Utility function for sorting by start times, falling back on end times
    """
    z = cmp(x.start, y.start)
    if not z:
        return cmp(x.end, y.end)
    return z
    
def unique_results(results):
    """ Utility function to create a sequence of unique calendar results
    """
    rids = {}
    for result in results:
        rids[result.getRID()] = result
    return rids.values()


class CalendarTool (UniqueObject, SimpleItem):

    """ A tool for encapsulating how calendars work and are displayed """

    id = 'portal_calendar'
    meta_type= 'CMF Calendar Tool'
    security = ClassSecurityInfo()

    implements(ICalendarTool)

    calendar_types = ('Event',)
    calendar_states = ('published',)
    use_session = False
    firstweekday = 6 # 6 is Sunday

    manage_options = (({'label' : 'Overview', 'action' : 'manage_overview'},
                       {'label' : 'Configure', 'action' : 'manage_configure'},
                      ) + SimpleItem.manage_options)

    #
    #   ZMI methods
    #
    security.declareProtected( ManagePortal, 'manage_overview' )
    manage_overview = PageTemplateFile('www/explainCalendarTool', globals(),
                                   __name__='manage_overview')

    security.declareProtected( ManagePortal, 'manage_configure' )
    manage_configure = PageTemplateFile('www/configureCalendarTool', globals(),
                                   __name__='manage_configure')

    security.declareProtected( ManagePortal, 'edit_configuration' )
    def edit_configuration( self
                          , show_types
                          , use_session
                          , show_states=None
                          , firstweekday=None
                          ):
        """ Change the configuration of the calendar tool 
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on self.REQUEST
        self.calendar_types = tuple(show_types)
        self.use_session = bool(use_session)

        if show_states is not None:
            self.calendar_states = tuple(show_states)

        if firstweekday is not None:
            try:
                fwd = int(firstweekday)

                if 0 <= fwd <= 6:
                    # Do nothing with illegal values
                    self.firstweekday = fwd
            except ValueError:
                # Do nothing with illegal values
                pass

        if hasattr(self.REQUEST, 'RESPONSE'):
            self.REQUEST.RESPONSE.redirect('manage_configure')

    security.declarePrivate('_getCalendar')
    def _getCalendar(self):
        """ Wrapper to ensure we set the first day of the week every time
        """
        calendar.setfirstweekday(self.getFirstWeekDay())
        return calendar

    security.declarePublic('getFirstWeekDay')
    def getFirstWeekDay(self):
        """ Get our first weekday setting
        """
        return self.firstweekday

    security.declarePublic('getCalendarTypes')
    def getCalendarTypes(self):
        """ Returns a list of type that will show in the calendar 
        """
        return self.calendar_types

    security.declarePublic('getCalendarStates')
    def getCalendarStates(self):
        """ Returns a list of workflow states that will show in the calendar 
        """
        return self.calendar_states

    security.declarePublic('getUseSession')
    def getUseSession(self):
        """ Returns the Use_Session option 
        """
        return bool(self.use_session)

    security.declarePublic('getDays')
    def getDays(self):
        """ Returns a list of days with the correct start day first 
        """
        return self._getCalendar().weekheader(2).split()

    security.declarePublic('getWeeksList')
    def getWeeksList(self, month='1', year='2002'):
        """ Return a series of weeks, each containing an integer day number.
        A day number of 0 means that day is in the previous or next month.
        """
        year = int(year)
        month = int(month)
        # daysByWeek is a list of days inside a list of weeks, like so:
        # [[0, 1, 2, 3, 4, 5, 6],
        #  [7, 8, 9, 10, 11, 12, 13],
        #  [14, 15, 16, 17, 18, 19, 20],
        #  [21, 22, 23, 24, 25, 26, 27],
        #  [28, 29, 30, 31, 0, 0, 0]]
        daysByWeek = self._getCalendar().monthcalendar(year, month)

        return daysByWeek

    security.declarePublic('getEventsForCalendar')
    def getEventsForCalendar(self, month='1', year='2002'):
        """ recreates a sequence of weeks, by days each day is a mapping.
            {'day': #, 'url': None}
        """
        year = int(year)
        month = int(month)
        # daysByWeek is a list of days inside a list of weeks, like so:
        # [[0, 1, 2, 3, 4, 5, 6],
        #  [7, 8, 9, 10, 11, 12, 13],
        #  [14, 15, 16, 17, 18, 19, 20],
        #  [21, 22, 23, 24, 25, 26, 27],
        #  [28, 29, 30, 31, 0, 0, 0]]
        daysByWeek = self._getCalendar().monthcalendar(year, month)
        weeks = []

        events = self.catalog_getevents(year, month)

        for week in daysByWeek:
            days = []
            for day in week:
                if events.has_key(day):
                    days.append(events[day])
                else:
                    days.append({'day': day, 'event': 0, 'eventslist':[]})

            weeks.append(days)

        return weeks

    security.declarePublic('catalog_getevents')
    def catalog_getevents(self, year, month):
        """ given a year and month return a list of days that have events 
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        year = int(year)
        month = int(month)
        last_day = self._getCalendar().monthrange(year, month)[1]
        first_date = self.getBeginAndEndTimes(1, month, year)[0]
        last_date = self.getBeginAndEndTimes(last_day, month, year)[1]

        ctool = getToolByName(self, 'portal_catalog')
        query = ctool(
                        portal_type=self.getCalendarTypes(),
                        review_state=self.getCalendarStates(),
                        start={'query': last_date, 'range': 'max'},
                        end={'query': first_date, 'range': 'min'},
                        sort_on='start' )

        # compile a list of the days that have events
        eventDays={}
        for daynumber in range(1, 32): # 1 to 31
            eventDays[daynumber] = {'eventslist': [],
                                    'event': 0,
                                    'day': daynumber}
        includedevents = []
        for result in query:
            if result.getRID() in includedevents:
                break
            else:
                includedevents.append(result.getRID())
            event={}
            # we need to deal with events that end next month
            if  result.end.greaterThan(last_date):
                eventEndDay = last_day
                event['end'] = None
            else:
                eventEndDay = result.end.day()
                if result.end == result.end.earliestTime():
                    event['end'] = (result.end - 1).latestTime().Time()
                else:
                    event['end'] = result.end.Time()
            # and events that started last month
            if result.start.lessThan(first_date):
                eventStartDay = 1
                event['start'] = None
            else:
                eventStartDay = result.start.day()
                event['start'] = result.start.Time()

            event['title'] = result.Title or result.getId

            if eventStartDay != eventEndDay:
                allEventDays = range(eventStartDay, eventEndDay+1)
                eventDays[eventStartDay]['eventslist'].append(
                        {'end': None,
                         'start': result.start.Time(),
                         'title': event['title']} )
                eventDays[eventStartDay]['event'] = 1

                for eventday in allEventDays[1:-1]:
                    eventDays[eventday]['eventslist'].append(
                        {'end': None,
                         'start': None,
                         'title': event['title']} )
                    eventDays[eventday]['event'] = 1

                if (result.end == result.end.earliestTime() and 
                    event['end'] is not None): 
                    # ends some day this month at midnight
                    last_day_data = eventDays[allEventDays[-2]]
                    last_days_event = last_day_data['eventslist'][-1]
                    last_days_event['end'] = (result.end-1).latestTime().Time()
                else:
                    eventDays[eventEndDay]['eventslist'].append( 
                        { 'end': event['end'],
                          'start': None,
                          'title': event['title']} )
                    eventDays[eventEndDay]['event'] = 1
            else:
                eventDays[eventStartDay]['eventslist'].append(event)
                eventDays[eventStartDay]['event'] = 1
            # This list is not uniqued and isn't sorted
            # uniquing and sorting only wastes time
            # and in this example we don't need to because
            # later we are going to do an 'if 2 in eventDays'
            # so the order is not important.
            # example:  [23, 28, 29, 30, 31, 23]
        return eventDays

    security.declarePublic('getEventsForThisDay')
    def getEventsForThisDay(self, thisDay):
        """ given an exact day return ALL events that:
            A) Start on this day  OR
            B) End on this day  OR
            C) Start before this day  AND  end after this day
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        day, month, year = ( int(thisDay.day())
                           , int(thisDay.month())
                           , int(thisDay.year())
                           )

        first_date, last_date = self.getBeginAndEndTimes(day, month, year)
        zone = first_date.localZone()
        after_midnight_str = '%d-%02d-%02d 00:01:00 %s' % (year,month,day,zone)
        after_midnight = DateTime(after_midnight_str)

        # Get all events that Start on this day
        ctool = getToolByName(self, 'portal_catalog')
        query = ctool(
                        portal_type=self.getCalendarTypes(),
                        review_state=self.getCalendarStates(),
                        start={'query': (first_date, last_date),
                               'range': 'minmax'} )

        # Get all events that End on this day
        query += ctool(
                         portal_type=self.getCalendarTypes(),
                         review_state=self.getCalendarStates(),
                         end={'query': (after_midnight, last_date),
                              'range': 'minmax'} )

        # Get all events that Start before this day AND End after this day
        query += ctool(
                         portal_type=self.getCalendarTypes(),
                         review_state=self.getCalendarStates(),
                         start={'query': first_date, 'range': 'max'},
                         end={'query': last_date, 'range': 'min'} )

        # Unique the results
        results = unique_results(query)

        # Sort by start date
        results.sort(sort_by_date)

        return results

    security.declarePublic('getPreviousMonth')
    def getPreviousMonth(self, month, year):
        """ Get a DateTime object for one month prior to the given year/month
        """
        month = int(month)
        year = int(year)

        if month == 0 or month == 1:
            month, year = 12, year - 1
        else:
            month -= 1

        return DateTime(year, month, 1)

    security.declarePublic('getNextMonth')
    def getNextMonth(self, month, year):
        """ Get a DateTime object for one month after the given year/month
        """
        month = int(month)
        year = int(year)

        if month == 12:
            month, year = 1, year + 1
        else:
            month += 1

        return DateTime(year, month, 1)

    security.declarePublic('getBeginAndEndTimes')
    def getBeginAndEndTimes(self, day, month, year):
        """ Get two DateTime objects representing the beginning and end
        of the given day
        """
        day = int(day)
        month = int(month)
        year = int(year)

        begin = DateTime('%d/%02d/%02d 00:00:00' % (year, month, day))
        end = DateTime('%d/%02d/%02d 23:59:59' % (year, month, day))

        return (begin, end)
        
    security.declarePublic('getNextEvent')
    def getNextEvent(self, start_date=None):
        """ Get the next event that starts after start_date
        
        start_date is expected to be a DateTime instance
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        if start_date is None:
            start_date = DateTime()

        ctool = getToolByName(self, 'portal_catalog')
        query = ctool(
                    portal_type=self.getCalendarTypes(),
                    review_state=self.getCalendarStates(),
                    start={'query': start_date, 'range': 'min'},
                    sort_on='start')

        results = unique_results(query)
        if results:
            results.sort(sort_by_date)
            return results[0]

InitializeClass(CalendarTool)
