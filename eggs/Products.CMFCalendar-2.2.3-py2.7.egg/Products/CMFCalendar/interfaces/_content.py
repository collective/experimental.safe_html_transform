##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFCalendar content interfaces.

$Id: _content.py 110663 2010-04-08 15:59:45Z tseaver $
"""

from zope.interface import Interface


class IEvent(Interface):

    """ IEvent models an event.
    """

    def getEndStrings():
        """ Returns a mapping with string representations for the end time

        o keys are 'day', 'month' and 'year'
        """

    def getStartStrings():
        """ Returns a mapping with string representations for the start time

        o keys are 'day', 'month' and 'year'
        """

    def start():
        """ Return our start time as a DateTime object
        """

    def end():
        """ Return our end time as a DateTime object
        """

    def getStartTimeString():
        """ Return our start time as a string.
        """

    def getStopTimeString():
        """ Return our stop time as a string.
        """

    def getMetadataHeaders():
        """ Return metadata attributes in RFC-822-style header spec.
        """

class IMutableEvent(IEvent):

    """ Updatable form of IEvent.
    """
    def edit( title=None
            , description=None
            , eventType=None
            , effectiveDay=None
            , effectiveMo=None
            , effectiveYear=None
            , expirationDay=None
            , expirationMo=None
            , expirationYear=None
            , start_time=None
            , startAMPM=None
            , stop_time=None
            , stopAMPM=None
            , location=None
            , contact_name=None
            , contact_email=None
            , contact_phone=None
            , event_url=None
            ):
        """ Update the event.

        o Only arguments that have a value are manipulated.
        """  

    def setStartDate(start):
        """ Setting the event start date when the event is scheduled to begin.
        """

    def setEndDate(end):
        """ Setting the event end date, when the event ends.
        """

    def setMetadata(headers):
        """ Set an Event's metadata

        o headers is a mapping containing keys corresponding to
        Dublin Core metadata fields
        o Only those attributes that are passed in with the mapping are
        manipulated
        """

