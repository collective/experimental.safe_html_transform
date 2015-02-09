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
""" Unit tests for CalendarTool module.

$Id: test_Calendar.py 110663 2010-04-08 15:59:45Z tseaver $
"""

import unittest
from Testing import ZopeTestCase
ZopeTestCase.utils.setupCoreSessions()

import locale

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
from DateTime import DateTime
from zope.interface.verify import verifyClass
from zope.site.hooks import setSite

from Products.CMFCalendar.testing import FunctionalLayer


class CalendarTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCalendar.CalendarTool import CalendarTool

        return CalendarTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCalendar.interfaces import ICalendarTool

        verifyClass(ICalendarTool, self._getTargetClass())

    def test_new(self):
        ctool = self._makeOne()
        self.assertEqual( ctool.getId(), 'portal_calendar' )

    def test_types(self):
        ctool = self._makeOne()
        self.assertEqual(ctool.getCalendarTypes(), ('Event',))

        ctool.edit_configuration(show_types=['Event','Party'],
                                 show_states=[],
                                 use_session="")
        self.assertEqual( ctool.getCalendarTypes(), ('Event', 'Party') )

    def test_states(self):
        ctool = self._makeOne()
        self.assertEqual(ctool.getCalendarStates(), ('published',))

        ctool.edit_configuration(show_types=[],
                                 show_states=['pending', 'published'],
                                 use_session="")
        self.assertEqual( ctool.getCalendarStates(), ('pending', 'published') )

    def test_days(self):
        ctool = self._makeOne()
        old_locale = locale.getlocale(locale.LC_ALL)[0]
        locale.setlocale(locale.LC_ALL, 'C')
        try:
            self.assertEqual( ctool.getDays(),
                              ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'] )
        finally:
            locale.setlocale(locale.LC_ALL, old_locale)

    def test_firstweekday(self):
        ctool = self._makeOne()
        ctool.firstweekday = 6
        self.assertEqual(ctool.getFirstWeekDay(), 6)

        # Try setting it to invalid values, the setting should not stick
        ctool.edit_configuration([], None, firstweekday='insane')
        self.assertEqual(ctool.getFirstWeekDay(), 6)

        ctool.edit_configuration([], None, firstweekday=42)
        self.assertEqual(ctool.getFirstWeekDay(), 6)

        # Set it to a sane value
        ctool.edit_configuration([], None, firstweekday=0)
        self.assertEqual(ctool.getFirstWeekDay(), 0)

        # Make sure the setting is being used...
        old_locale = locale.getlocale(locale.LC_ALL)[0]
        locale.setlocale(locale.LC_ALL, 'C')
        try:
            self.assertEqual( ctool.getDays(),
                              ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa','Su'] )
        finally:
            locale.setlocale(locale.LC_ALL, old_locale)


class CalendarRequestTests(ZopeTestCase.FunctionalTestCase):

    layer = FunctionalLayer

    def afterSetUp(self):
        setSite(self.app.site)
        self.app.site.setupCurrentSkin(self.app.REQUEST)
        newSecurityManager(None, UnrestrictedUser('god', '', ['Manager'], ''))

        # sessioning setup
        sdm = self.app.session_data_manager
        self.app.REQUEST.set_lazy('SESSION', sdm.getSessionData)

    def _testURL(self, url, params=None):
        obj = self.app.site.restrictedTraverse(url)
        if params is None:
            params=(obj, self.app.site.REQUEST)
        obj(*params)

    def test_sessions_skinsview(self):
        caltool = self.app.site.portal_calendar
        caltool.edit_configuration(show_types=['Event'], use_session="True")
        self._testURL('/site/calendarBox', ())

        self.failUnless(self.app.REQUEST.SESSION.get('calendar_year',None))

    def test_sessions_fiveview(self):
        caltool = self.app.site.portal_calendar
        caltool.edit_configuration(show_types=['Event'], use_session="True")
        self._testURL('/site/@@calendar_widget', ())

        self.failUnless(self.app.REQUEST.SESSION.get('calendar_year',None))

    def test_noSessions_skinsview(self):
        caltool = self.app.site.portal_calendar
        caltool.edit_configuration(show_types=['Event'], use_session="")
        self._testURL('/site/calendarBox', ())

        self.failIf(self.app.REQUEST.SESSION.get('calendar_year',None))

    def test_noSessions_fiveview(self):
        caltool = self.app.site.portal_calendar
        caltool.edit_configuration(show_types=['Event'], use_session="")
        self._testURL('/site/@@calendar_widget', ())

        self.failIf(self.app.REQUEST.SESSION.get('calendar_year',None))

    def test_simpleCalendarRendering(self):
        caltool = self.app.site.portal_calendar
        data = [
                [
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 1, 'event': 0, 'eventslist':[]},
                 {'day': 2, 'event': 0, 'eventslist':[]},
                 {'day': 3, 'event': 0, 'eventslist':[]},
                 {'day': 4, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day': 5, 'event': 0, 'eventslist':[]},
                 {'day': 6, 'event': 0, 'eventslist':[]},
                 {'day': 7, 'event': 0, 'eventslist':[]},
                 {'day': 8, 'event': 0, 'eventslist':[]},
                 {'day': 9, 'event': 0, 'eventslist':[]},
                 {'day':10, 'event': 0, 'eventslist':[]},
                 {'day':11, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day':12, 'event': 0, 'eventslist':[]},
                 {'day':13, 'event': 0, 'eventslist':[]},
                 {'day':14, 'event': 0, 'eventslist':[]},
                 {'day':15, 'event': 0, 'eventslist':[]},
                 {'day':16, 'event': 0, 'eventslist':[]},
                 {'day':17, 'event': 0, 'eventslist':[]},
                 {'day':18, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day':19, 'event': 0, 'eventslist':[]},
                 {'day':20, 'event': 0, 'eventslist':[]},
                 {'day':21, 'event': 0, 'eventslist':[]},
                 {'day':22, 'event': 0, 'eventslist':[]},
                 {'day':23, 'event': 0, 'eventslist':[]},
                 {'day':24, 'event': 0, 'eventslist':[]},
                 {'day':25, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day':26, 'event': 0, 'eventslist':[]},
                 {'day':27, 'event': 0, 'eventslist':[]},
                 {'day':28, 'event': 0, 'eventslist':[]},
                 {'day':29, 'event': 0, 'eventslist':[]},
                 {'day':30, 'event': 0, 'eventslist':[]},
                 {'day':31, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 ]
                ]
        result = caltool.getEventsForCalendar(month='5', year='2002')
        self.assertEqual(result, data)

    def test_singleEventCalendarRendering(self):
        site = self.app.site
        caltool = self.app.site.portal_calendar
        site.Members.invokeFactory(type_name="Event",id='Event1')
        event = self.app.restrictedTraverse('/site/Members/Event1')
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=1
                    , effectiveMo=5
                    , effectiveYear=2002
                    , expirationDay=1
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        site.portal_workflow.doActionFor(event, 'publish', comment='testing')

        data = [
                [
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 1, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': '23:59:00',
                                                       'start': '00:00:00'}]},
                 {'day': 2, 'event': 0, 'eventslist':[]},
                 {'day': 3, 'event': 0, 'eventslist':[]},
                 {'day': 4, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day': 5, 'event': 0, 'eventslist':[]},
                 {'day': 6, 'event': 0, 'eventslist':[]},
                 {'day': 7, 'event': 0, 'eventslist':[]},
                 {'day': 8, 'event': 0, 'eventslist':[]},
                 {'day': 9, 'event': 0, 'eventslist':[]},
                 {'day':10, 'event': 0, 'eventslist':[]},
                 {'day':11, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day':12, 'event': 0, 'eventslist':[]},
                 {'day':13, 'event': 0, 'eventslist':[]},
                 {'day':14, 'event': 0, 'eventslist':[]},
                 {'day':15, 'event': 0, 'eventslist':[]},
                 {'day':16, 'event': 0, 'eventslist':[]},
                 {'day':17, 'event': 0, 'eventslist':[]},
                 {'day':18, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day':19, 'event': 0, 'eventslist':[]},
                 {'day':20, 'event': 0, 'eventslist':[]},
                 {'day':21, 'event': 0, 'eventslist':[]},
                 {'day':22, 'event': 0, 'eventslist':[]},
                 {'day':23, 'event': 0, 'eventslist':[]},
                 {'day':24, 'event': 0, 'eventslist':[]},
                 {'day':25, 'event': 0, 'eventslist':[]},
                 ],
                [
                 {'day':26, 'event': 0, 'eventslist':[]},
                 {'day':27, 'event': 0, 'eventslist':[]},
                 {'day':28, 'event': 0, 'eventslist':[]},
                 {'day':29, 'event': 0, 'eventslist':[]},
                 {'day':30, 'event': 0, 'eventslist':[]},
                 {'day':31, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 ]
                ]
        result = caltool.getEventsForCalendar(month='5', year='2002')
        self.assertEqual(result, data)

    def test_eventCalendarRenderingIssue411(self):
        #  http://www.zope.org/Collectors/CMF/411
        site = self.app.site
        site.Members.invokeFactory(type_name="Event",id='Event1')
        event = self.app.restrictedTraverse('/site/Members/Event1')
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=31
                    , effectiveMo=3
                    , effectiveYear=2006
                    , expirationDay=1
                    , expirationMo=4
                    , expirationYear=2006
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="00:00"
                    , stopAMPM="AM"
                    )
        site.portal_workflow.doActionFor(event, 'publish', comment='testing')

        site.Members.invokeFactory(type_name="Event",id='Event2')
        event = self.app.restrictedTraverse('/site/Members/Event2')
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=29
                    , effectiveMo=3
                    , effectiveYear=2006
                    , expirationDay=30
                    , expirationMo=3
                    , expirationYear=2006
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="00:00"
                    , stopAMPM="AM"
                    )
        site.portal_workflow.doActionFor(event, 'publish', comment='testing')

        # With the bug unfixed, this raises a TypeError
        ignored = site.portal_calendar.catalog_getevents(2006, 3)

    def test_spanningEventCalendarRendering(self):
        site = self.app.site
        caltool = self.app.site.portal_calendar
        site.Members.invokeFactory(type_name="Event",id='Event1')
        event = self.app.restrictedTraverse('/site/Members/Event1')
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=1
                    , effectiveMo=5
                    , effectiveYear=2002
                    , expirationDay=31
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        site.portal_workflow.doActionFor(event, 'publish', comment='testing')

        data = [
                [
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                 {'day': 1, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': '00:00:00'}]},
                 {'day': 2, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day': 3, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day': 4, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                ],
                [
                 {'day': 5, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day': 6, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day': 7, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day': 8, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day': 9, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':10, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':11, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                ],
                [
                 {'day':12, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':13, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':14, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':15, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':16, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':17, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':18, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                ],
                [
                 {'day':19, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':20, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':21, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':22, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':23, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':24, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':25, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 ],
                [
                 {'day':26, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':27, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':28, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':29, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':30, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': None,
                                                       'start': None}]},
                 {'day':31, 'event': 1, 'eventslist':[{'title': 'title',
                                                       'end': '23:59:00',
                                                       'start': None}]},
                 {'day': 0, 'event': 0, 'eventslist':[]},
                ]
               ]
        result = caltool.getEventsForCalendar(month='5', year='2002')
        self.assertEqual(result, data)

    def test_getPreviousMonth(self):
        caltool = self.app.site.portal_calendar

        self.assertEqual( caltool.getPreviousMonth(2,2002),
                          DateTime('2002/1/1') )
        self.assertEqual( caltool.getPreviousMonth(1,2002),
                          DateTime('2001/12/1') )

    def test_getNextMonth(self):
        caltool = self.app.site.portal_calendar

        self.assertEqual( caltool.getNextMonth(12,2001),
                          DateTime('2002/1/1') )
        self.assertEqual( caltool.getNextMonth(1,2002),
                          DateTime('2002/2/1') )

    def test_getBeginAndEndTimes(self):
        caltool = self.app.site.portal_calendar

        self.assertEqual( caltool.getBeginAndEndTimes(1,12,2001),
                          ( DateTime('2001/12/1 12:00:00AM'),
                            DateTime('2001/12/1 11:59:59PM') ) )

    def test_singleDayRendering(self):
        site = self.app.site
        caltool = self.app.site.portal_calendar
        wftool = self.app.site.portal_workflow

        site.Members.invokeFactory(type_name="Event",id='Event1')
        event = site.Members.Event1
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=1
                    , effectiveMo=5
                    , effectiveYear=2002
                    , expirationDay=31
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        wftool.doActionFor(event, 'publish', comment='testing')
        events = caltool.getEventsForThisDay(thisDay=DateTime('2002/5/1'))
        self.assertEqual( len(events), 1 )

        site.Members.invokeFactory(type_name="Event",id='Event2')
        event = site.Members.Event2
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=1
                    , effectiveMo=5
                    , effectiveYear=2002
                    , expirationDay=1
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        wftool.doActionFor(event, 'publish', comment='testing')
        events = caltool.getEventsForThisDay(thisDay=DateTime('2002/5/1'))
        self.assertEqual( len(events), 2 )

        site.Members.invokeFactory(type_name="Event",id='Event3')
        event = site.Members.Event3
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=12
                    , effectiveMo=12
                    , effectiveYear=2001
                    , expirationDay=1
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        wftool.doActionFor(event, 'publish', comment='testing')
        events = caltool.getEventsForThisDay(thisDay=DateTime('2002/5/1'))
        self.assertEqual( len(events), 3 )

        site.Members.invokeFactory(type_name="Event",id='Event4')
        event = site.Members.Event4
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=12
                    , effectiveMo=12
                    , effectiveYear=2001
                    , expirationDay=31
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        wftool.doActionFor(event, 'publish', comment='testing')
        events = caltool.getEventsForThisDay(thisDay=DateTime('2002/5/1'))
        self.assertEqual( len(events), 4 )

        site.Members.invokeFactory(type_name="Event",id='Event5')
        event = site.Members.Event5
        event.edit( title='title'
                    , description='description'
                    , eventType=( 'eventType', )
                    , effectiveDay=31
                    , effectiveMo=5
                    , effectiveYear=2002
                    , expirationDay=31
                    , expirationMo=5
                    , expirationYear=2002
                    , start_time="00:00"
                    , startAMPM="AM"
                    , stop_time="11:59"
                    , stopAMPM="PM"
                    )
        wftool.doActionFor(event, 'publish', comment='testing')
        events = caltool.getEventsForThisDay(thisDay=DateTime('2002/5/1'))
        self.assertEqual( len(events), 4 )
        events = caltool.getEventsForThisDay(thisDay=DateTime('2002/5/31'))
        self.assertEqual( len(events), 3 )

    def test_veryLongEvent(self):
        # Proper handling of events that last more than 1 year
        # and end in the same month
        site = self.app.site
        site.invokeFactory('Event', id='long', title='A long event',
                           start_date='2007/10/12 00:00:00',
                           end_date='2008/10/12 00:00:00')
        site.portal_workflow.doActionFor(site.long, 'publish')
        expected = {'eventslist': [{'start': None, 'end': None, 
                                    'title': 'A long event'}], 
                                    'event': 1, 'day': 13}
        events = site.portal_calendar.catalog_getevents(2007, 10)
        self.assertEqual(events[13], expected)
        
    def test_lastDayRenderingOfLongEvent(self):
        # Bug in catalog_getevents doesn't include events
        # that spawn over months in the last day of each month
        site = self.app.site
        site.invokeFactory('Event', id='long', title='A long event',
                           start_date='2007/10/12 23:50:00',
                           end_date='2008/03/20 00:00:00')

        site.portal_workflow.doActionFor(site.long, 'publish')
        expected = {'eventslist': [{'start': None, 'end': None, 
                                    'title': 'A long event'}], 
                                    'event': 1}
        # some dates to try: (day,month,year)
        dates = ( (30,10,2007), (31,10,2007), (29,11,2007), (30,11,2007),
                  (30,12,2007), (31,12,2007), (28,2,2008), (28,2,2008) )
        for (day,month,year) in dates:
            events = site.portal_calendar.catalog_getevents(year, month)
            expected['day'] = day
            self.assertEqual(events[day], expected)

    def test_lastDayRendering(self):
        # Bug in catalog_getevents included events starting at 00:00:00
        # on the next day
        site = self.app.site
        site.invokeFactory('Event', id='today', title='today',
                           start_date='2002/05/31 23:50:00',
                           end_date='2002/05/31 23:59:59')

        site.invokeFactory('Event', id='tomorrow', title='tomorrow',
                           start_date='2002/06/01 00:00:00',
                           end_date='2002/06/01 00:10:00')

        site.portal_workflow.doActionFor(site.today, 'publish')
        site.portal_workflow.doActionFor(site.tomorrow, 'publish')

        # Last week of May 2002
        data = [
               {'day': 25, 'event': 0, 'eventslist':[]},
               {'day': 26, 'event': 0, 'eventslist':[]},
               {'day': 27, 'event': 0, 'eventslist':[]},
               {'day': 28, 'event': 0, 'eventslist':[]},
               {'day': 29, 'event': 0, 'eventslist':[]},
               {'day': 30, 'event': 0, 'eventslist':[]},
               {'day': 31, 'event': 1, 'eventslist':[{'start': '23:50:00',
                                                      'end': '23:59:59',
                                                      'title': 'today'}]},
               ]

        events = site.portal_calendar.catalog_getevents(2002, 5)
        self.assertEqual([events[e] for e in range(25, 32)], data)

    def test_firstDayRendering(self):
        # Double check it works on the other boundary as well
        site = self.app.site
        site.invokeFactory('Event', id='yesterday', title='yesterday',
                           start_date='2002/05/31 23:50:00',
                           end_date='2002/05/31 23:59:59')

        site.invokeFactory('Event', id='today', title='today',
                           start_date='2002/06/01 00:00:00',
                           end_date='2002/06/01 00:10:00')

        site.portal_workflow.doActionFor(site.yesterday, 'publish')
        site.portal_workflow.doActionFor(site.today, 'publish')

        # First week of June 2002
        data = [
               {'day': 1, 'event': 1, 'eventslist':[{'start': '00:00:00',
                                                     'end': '00:10:00',
                                                     'title': 'today'}]},
               {'day': 2, 'event': 0, 'eventslist':[]},
               {'day': 3, 'event': 0, 'eventslist':[]},
               {'day': 4, 'event': 0, 'eventslist':[]},
               {'day': 5, 'event': 0, 'eventslist':[]},
               {'day': 6, 'event': 0, 'eventslist':[]},
               {'day': 7, 'event': 0, 'eventslist':[]},
               ]

        events = site.portal_calendar.catalog_getevents(2002, 6)
        self.assertEqual([events[e] for e in range(1, 8)], data)

    def test_workflowStateRendering(self):
        # Calendar should return events in all of the selected workflow states
        site = self.app.site
        caltool = self.app.site.portal_calendar
        site.invokeFactory('Event', id='meeting',
                           start_date='2002/05/01 11:00:00',
                           end_date='2002/05/01 13:30:00')

        site.invokeFactory('Event', id='dinner',
                           start_date='2002/05/01 20:00:00',
                           end_date='2002/05/01 22:00:00')

        self.assertEqual(len(site.portal_catalog(portal_type='Event')), 2)

        # No published events
        self.assertEqual(
            len(caltool.getEventsForThisDay(DateTime('2002/05/01'))), 0)

        # One published event
        site.portal_workflow.doActionFor(site.meeting, 'publish')
        self.assertEqual(len(site.portal_catalog(review_state='published')), 1)

        self.assertEqual(
            len(caltool.getEventsForThisDay(DateTime('2002/05/01'))), 1)

        # One pending event
        site.portal_workflow.doActionFor(site.dinner, 'submit')
        self.assertEqual(len(site.portal_catalog(review_state='pending')), 1)

        self.assertEqual(
            len(caltool.getEventsForThisDay(DateTime('2002/05/01'))), 1)

        # Make calendar return pending events
        caltool.edit_configuration(show_types=('Event',),
                                   show_states=('pending', 'published'),
                                   use_session='')

        self.assertEqual(
            len(caltool.getEventsForThisDay(DateTime('2002/05/01'))), 2)

    def test_EventEndingMidnight(self):
        # Events ending exactly at midnight should not be shown for the day
        # after (see http://www.zope.org/Collectors/CMF/246)
        site = self.app.site
        caltool = self.app.site.portal_calendar
        the_day = DateTime('2002/05/01')
        day_after = DateTime('2002/05/02')

        site.invokeFactory('Event', id='party',
                           start_date=the_day,
                           end_date=day_after)
        site.portal_workflow.doActionFor(site.party, 'publish')

        # One entry should be present for the day of the event
        self.assertEqual(len(caltool.getEventsForThisDay(the_day)), 1)

        # No entry should be present for the day after
        self.assertEqual(len(caltool.getEventsForThisDay(day_after)), 0)

        # First week of May 2002
        data = [
               {'day': 1, 'event': 1, 'eventslist':[{'start': '00:00:00',
                                                     'end': '23:59:59',
                                                     'title': 'party'}]},
               {'day': 2, 'event': 0, 'eventslist':[]},
               {'day': 3, 'event': 0, 'eventslist':[]},
               {'day': 4, 'event': 0, 'eventslist':[]},
               {'day': 5, 'event': 0, 'eventslist':[]},
               {'day': 6, 'event': 0, 'eventslist':[]},
               {'day': 7, 'event': 0, 'eventslist':[]},
               ]

        events = caltool.catalog_getevents(2002, 5)
        self.assertEqual([events[e] for e in range(1, 8)], data)

    def test_getNextEvent(self):
        cal = self.app.site.portal_calendar
        wf_tool = self.app.site.portal_workflow
        start_one = DateTime('2002/05/01 19:30:00 GMT+1')
        stop_one = DateTime('2002/05/01 22:00:00 GMT+1')
        start_two = DateTime('2002/06/01 19:30:00 GMT+1')
        stop_two = DateTime('2002/06/01 22:00:00 GMT+1')

        test_day = DateTime('2002/07/01')

        self.app.site.invokeFactory( 'Event'
                                   , id='party1'
                                   , start_date=start_one
                                   , end_date=stop_one
                                   )


        self.app.site.invokeFactory( 'Event'
                                   , id='party2'
                                   , start_date=start_two
                                   , end_date=start_two
                                   )

        wf_tool.doActionFor(self.app.site.party1, 'publish')
        wf_tool.doActionFor(self.app.site.party2, 'publish')

        # Check to see if we get only one event when back
        self.assertEqual(cal.getNextEvent(stop_one).start, start_two)

        # Check to see that we don't have events after July 2002
        self.failIf(cal.getNextEvent(test_day))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CalendarTests),
        unittest.makeSuite(CalendarRequestTests),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
