##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for Event module.

$Id: test_Event.py 121612 2011-05-08 16:52:46Z hannosch $
"""

import unittest
import Testing

from DateTime import DateTime
from DateTime.interfaces import DateError
from zope.interface.verify import verifyClass

from Products.CMFCore.testing import ConformsToContent
from Products.CMFCore.tests.base.testcase import RequestTest


class TestEvent(ConformsToContent, unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCalendar.Event import Event

        return Event

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCalendar.interfaces import IEvent
        from Products.CMFCalendar.interfaces import IMutableEvent

        verifyClass(IEvent, self._getTargetClass())
        verifyClass(IMutableEvent, self._getTargetClass())

    def test_new(self):
        event = self._makeOne('test')

        self.assertEqual( event.getId(), 'test' )
        self.failIf( event.Title() )

    def test_edit(self):
        # Year month and day were processed in the wrong order
        # Also see http://collector.zope.org/CMF/202
        event = self._makeOne('foo')
        event.edit( title='title'
                  , description='description'
                  , eventType=( 'eventType', )
                  , effectiveDay=1
                  , effectiveMo=5
                  , effectiveYear=1999
                  , expirationDay=31
                  , expirationMo=12
                  , expirationYear=1999
                  , start_time="00:00"
                  , startAMPM="AM"
                  , stop_time="11:59"
                  , stopAMPM="PM"
                  )

        self.assertEqual( event.Title(), 'title' )
        self.assertEqual( event.Description(), 'description' )
        self.assertEqual( event.Subject(), ( 'eventType', ), event.Subject() )
        self.assertEqual( event.effective_date, None )
        self.assertEqual( event.expiration_date, None )
        self.assertEqual( event.end(), DateTime('1999/12/31 23:59') )
        self.assertEqual( event.start(), DateTime('1999/05/01 00:00') )
        self.failIf( event.contact_name )

    def test_puke(self):
        event = self._makeOne('shouldPuke')

        self.assertRaises( DateError
                         , event.edit
                         , effectiveDay=31
                         , effectiveMo=2
                         , effectiveYear=1999
                         , start_time="00:00"
                         , startAMPM="AM"
                         )

EVENT_TXT = """\
Title: Test Event
Subject: Foosubject
Contributors: Jim
Effective_date: 2002-01-01T00:00:00Z
Expiration_date: 2009-12-31T00:00:00Z
StartDate: 2006/02/23 18:00
EndDate: 2006/02/23 23:00
Location: Spuds and Suds, River Street, Anytown
Language: French
Rights: Anytown Gazetteer
ContactName: Jim
ContactEmail: jim@example.com
ContactPhone: (888) 555-1212
EventURL: http://www.example.com
Creator: Jim

Fundraiser for disabled goldfish
"""

class EventPUTTests(RequestTest):

    def _makeOne(self, id, *args, **kw):
        from Products.CMFCalendar.Event import Event

        # NullResource.PUT calls the PUT method on the bare object!
        return Event(id, *args, **kw)

    def test_PutWithoutMetadata(self):
        self.REQUEST['BODY'] = ''
        d = self._makeOne('foo')
        d.PUT(self.REQUEST, self.RESPONSE)

        self.assertEqual( d.Title(), '' )
        self.assertEqual( d.Format(), 'text/plain' )
        self.assertEqual( d.Description(), '' )
        self.assertEqual( d.Subject(), () )
        self.assertEqual( d.Contributors(), () )
        self.assertEqual( d.EffectiveDate('UTC'), 'None' )
        self.assertEqual( d.ExpirationDate('UTC'), 'None' )
        self.assertEqual( d.Language(), '' )
        self.assertEqual( d.Rights(), '' )
        self.assertEqual( d.location, '' )
        self.assertEqual( d.contact_name, '' )
        self.assertEqual( d.contact_email, '' )
        self.assertEqual( d.contact_phone, '' )
        self.assertEqual( d.event_url, '' )

    def test_PutWithMetadata(self):
        self.REQUEST['BODY'] = EVENT_TXT
        self.REQUEST.environ['CONTENT_TYPE'] = 'text/html'
        d = self._makeOne('foo')
        d.PUT(self.REQUEST, self.RESPONSE)

        self.assertEqual( d.Title(), 'Test Event' )
        self.assertEqual( d.Format(), 'text/html' )
        self.assertEqual( d.Description().strip()
                        , 'Fundraiser for disabled goldfish'
                        )
        self.assertEqual( d.Subject(), ('Foosubject',) )
        self.assertEqual( d.Contributors(), ('Jim',) )
        self.assertEqual( d.EffectiveDate('UTC'), '2002-01-01 00:00:00' )
        self.assertEqual( d.ExpirationDate('UTC'), '2009-12-31 00:00:00' )
        self.assertEqual( d.Language(), 'French' )
        self.assertEqual( d.Rights(), 'Anytown Gazetteer' )
        self.assertEqual( d.location, 'Spuds and Suds, River Street, Anytown' )
        self.assertEqual( d.contact_name, 'Jim' )
        self.assertEqual( d.contact_email, 'jim@example.com' )
        self.assertEqual( d.contact_phone, '(888) 555-1212' )
        self.assertEqual( d.event_url, 'http://www.example.com' )
        self.assertEqual( d.start(), DateTime('2006/02/23 18:00') )
        self.assertEqual( d.end(), DateTime('2006/02/23 23:00') )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestEvent),
        unittest.makeSuite(EventPUTTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
