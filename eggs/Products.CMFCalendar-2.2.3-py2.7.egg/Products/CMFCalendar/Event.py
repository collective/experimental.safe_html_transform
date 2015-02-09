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
""" Event: A CMF-enabled Event object.

$Id: Event.py 110663 2010-04-08 15:59:45Z tseaver $
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from DateTime.DateTime import DateTime
import transaction
from zope.component.factory import Factory
from zope.interface import implements

from Products.CMFCalendar.exceptions import ResourceLockedError
from Products.CMFCalendar.interfaces import IEvent
from Products.CMFCalendar.interfaces import IMutableEvent
from Products.CMFCalendar.permissions import ChangeEvents
from Products.CMFCalendar.permissions import ModifyPortalContent
from Products.CMFCalendar.permissions import View
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.utils import contributorsplitter
from Products.CMFCore.utils import keywordsplitter
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDefault.utils import bodyfinder
from Products.CMFDefault.utils import formatRFC822Headers
from Products.CMFDefault.utils import html_headcheck
from Products.CMFDefault.utils import parseHeadersBody
from Products.CMFDefault.utils import SimpleHTMLParser
from Products.GenericSetup.interfaces import IDAVAware

def addEvent( self
            , id
            , title=''
            , description=''
            , effective_date = None 
            , expiration_date = None 
            , start_date = None 
            , end_date = None
            , location=''
            , contact_name=''
            , contact_email=''
            , contact_phone=''
            , event_url=''
            , REQUEST=None
            ):
    """Create an empty event.
    """
    event = Event( id
                 , title
                 , description
                 , effective_date
                 , expiration_date
                 , start_date
                 , end_date
                 , location
                 , contact_name
                 , contact_email
                 , contact_phone
                 , event_url
                 )
    self._setObject(id, event, suppress_events=True)

def _dateStrings( when ):

    strings = {}

    if when is not None:
        strings[ 'year' ]   = str( when.year() )
        strings[ 'month' ]  = str( when.month() )
        strings[ 'day' ]    = str( when.day() )
    else:
        strings[ 'year' ]   = ''
        strings[ 'month' ]  = ''
        strings[ 'day' ]    = ''

    return strings


class Event(PortalContent, DefaultDublinCoreImpl):

    """Events are objects for the Calendar topical query.
    """

    # Declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    implements(IMutableEvent, IEvent, IDAVAware)

    def __init__( self
                , id
                , title=''
                , description=''
                , effective_date = None 
                , expiration_date = None 
                , start_date = None
                , end_date = None
                , location=''
                , contact_name=''
                , contact_email=''
                , contact_phone=''
                , event_url=''
                ):
        DefaultDublinCoreImpl.__init__(self)
        self.id=id
        self.setTitle(title)
        self.setDescription(description)
        self.effective_date = effective_date
        self.expiration_date = expiration_date
        self.setStartDate(start_date)

        if start_date is None:
            start_date = DateTime()
        if end_date is None:
            end_date = start_date

        if end_date < start_date:
            end_date = start_date

        self.setEndDate(end_date)
        self.location=location
        self.contact_name=contact_name
        self.contact_email=contact_email
        self.contact_phone=contact_phone
        self.event_url=event_url

    security.declarePrivate( '_datify' )
    def _datify( self, attrib ):
        if attrib == 'None':
            attrib = None
        elif not isinstance( attrib, DateTime ):
            if attrib is not None:
                attrib = DateTime( attrib )
        return attrib

    security.declarePublic('getEndStrings')
    def getEndStrings(self):
        """ Returns a mapping with string representations for the end time

        o keys are 'day', 'month' and 'year'
        """
        return _dateStrings(self.end())

    security.declarePublic('getStartStrings')
    def getStartStrings(self):
        """ Returns a mapping with string representations for the start time

        o keys are 'day', 'month' and 'year'
        """
        return _dateStrings(self.start())

    security.declareProtected(ChangeEvents, 'edit')
    def edit( self
            , title=None
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
        """\
        """

        if title is not None: 
            self.setTitle(title)
        if description is not None:
            self.setDescription(description)
        if eventType is not None:
            self.setSubject(eventType)

        start_date = end_date = None

        if effectiveDay and effectiveMo and effectiveYear and start_time:
            efdate = '%s/%s/%s %s %s' % (effectiveYear
                                         , effectiveMo
                                         , effectiveDay
                                         , start_time
                                         , startAMPM
                                         )
            start_date = DateTime( efdate )

        if expirationDay and expirationMo and expirationYear and stop_time:

            exdate = '%s/%s/%s %s %s' % (expirationYear
                                         , expirationMo
                                         , expirationDay
                                         , stop_time
                                         , stopAMPM
                                         )
            end_date = DateTime( exdate )

        if start_date and end_date:

            if end_date < start_date:
                end_date = start_date

            self.setStartDate( start_date )
            self.setEndDate( end_date )

        if location is not None:
            self.location = location
        if contact_name is not None:
            self.contact_name = contact_name
        if contact_email is not None:
            self.contact_email = contact_email
        if contact_phone is not None:
            self.contact_phone = contact_phone
        if event_url is not None:
            self.event_url = event_url
        self.reindexObject()

    security.declarePublic('buildTimes')
    def buildTimes(self):
        result = []
        for hour in range (1, 13):
            for min in (00, 30):
                result.append('%02d:%02d' % (hour, min))
        return result

    security.declarePublic('buildDays')
    def buildDays(self):
        result = []
        for day in range (1, 32):
            result.append(str('%d' % (day)))
        return result

    security.declarePublic('buildMonths')
    def buildMonths(self):
        result = []
        for month in range (1, 13):
            result.append(str('%d' % (month)))
        return result

    security.declarePublic('buildYears')
    def buildYears(self):
        result = []
        start = (DateTime().year() - 2)
        end = (DateTime().year() + 5)
        for year in range (start, end):
            result.append(str(year))
        return result

    security.declareProtected(ChangeEvents, 'setStartDate')
    def setStartDate(self, start):
        """ Setting the event start date when the event is scheduled to begin.
        """
        self.start_date = self._datify(start)

    security.declareProtected(ChangeEvents, 'setEndDate')
    def setEndDate(self, end):
        """ Setting the event end date, when the event ends.
        """
        self.end_date = self._datify(end)

    security.declarePublic('start')
    def start(self):
        """ Return our start time as a DateTime object
        """
        date = getattr( self, 'start_date', None )
        return date is None and self.created() or date

    security.declarePublic('end')
    def end(self):
        """ Return our end time as a DateTime object
        """
        date = getattr( self, 'end_date', None )
        return date is None and self.start() or date

    security.declarePublic('getStartTimeString')
    def getStartTimeString( self ):
        """ Return our start time as a string.
        """
        return self.start().AMPMMinutes() 

    security.declarePublic('getStopTimeString')
    def getStopTimeString( self ):
        """ Return our stop time as a string.
        """
        return self.end().AMPMMinutes() 

    security.declarePrivate('handleText')
    def handleText(self, text, format=None):
        """ Handles the raw text, returning headers, body, cooked, format """
        headers = {}
        if format == 'html':
            parser = SimpleHTMLParser()
            parser.feed(text)
            headers.update(parser.metatags)
            if parser.title:
                headers['Title'] = parser.title
            bodyfound = bodyfinder(text)
            if bodyfound:
                body = bodyfound
        else:
            headers, body = parseHeadersBody(text, headers)

        return headers, body, format

    security.declareProtected(ModifyPortalContent, 'setMetadata')
    def setMetadata(self, headers):
        """ Set an Event's metadata

        o headers is a mapping containing keys corresponding to
        Dublin Core metadata fields
        o Only those attributes that are passed in with the mapping are
        manipulated
        """
        headers['Format'] = self.Format()
        new_subject = keywordsplitter(headers)
        headers['Subject'] = new_subject or self.Subject()
        new_contrib = contributorsplitter(headers)
        headers['Contributors'] = new_contrib or self.Contributors()
        haveheader = headers.has_key
        for key, value in self.getMetadataHeaders():
            if not haveheader(key):
                headers[key] = value
        self._editMetadata(title=headers['Title'],
                          subject=headers['Subject'],
                          contributors=headers['Contributors'],
                          effective_date=headers['Effective_date'],
                          expiration_date=headers['Expiration_date'],
                          format=headers['Format'],
                          language=headers['Language'],
                          rights=headers['Rights'],
                          )

    security.declarePublic( 'getMetadataHeaders' )
    def getMetadataHeaders(self):
        """ Return metadata attributes in RFC-822-style header spec.
        """
        fmt = '%Y-%m-%d %H:%M:%S'
        hdrlist = [x for x in DefaultDublinCoreImpl.getMetadataHeaders(self)
                         if x[0] != 'Description']
        hdrlist.append(('Startdate', self.start().strftime(fmt)))
        hdrlist.append(('Enddate',  self.end().strftime(fmt)))
        hdrlist.append(('Location', self.location))
        hdrlist.append(('Contactname', self.contact_name))
        hdrlist.append(('Contactemail', self.contact_email))
        hdrlist.append(('Contactphone', self.contact_phone))
        hdrlist.append(('Eventurl', self.event_url))

        return hdrlist

    ## FTP handlers

    security.declareProtected(ModifyPortalContent, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """ Handle HTTP (and presumably FTP?) PUT requests """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        body = REQUEST.get('BODY', '')
        guessedformat = REQUEST.get_header('Content-Type', 'text/plain')
        ishtml = (guessedformat == 'text/html') or html_headcheck(body)

        if ishtml: self.setFormat('text/html')
        else: self.setFormat('text/plain')

        try:
            headers, body, format = self.handleText(text=body)
            self.setMetadata(headers)
            self.setStartDate(headers['Startdate'])
            self.setEndDate(headers['Enddate'])
            self.edit( location=headers['Location']
             , contact_name=headers['Contactname']
             , contact_email=headers['Contactemail']
             , contact_phone=headers['Contactphone']
             , event_url=headers['Eventurl']
             , description=body
             )

        except ResourceLockedError, msg:
            transaction.abort()
            RESPONSE.setStatus(423)
            return RESPONSE

        RESPONSE.setStatus(204)
        self.reindexObject()
        return RESPONSE

    security.declareProtected(View, 'manage_FTPget')
    def manage_FTPget(self):
        "Get the document body for FTP download (also used for the WebDAV SRC)"
        hdrlist = self.getMetadataHeaders()
        hdrtext = formatRFC822Headers( hdrlist )
        bodytext = '%s\r\n\r\n%s' % ( hdrtext, self.Description() )

        return bodytext

    security.declareProtected(View, 'get_size')
    def get_size( self ):
        """ Used for FTP and apparently the ZMI now too """
        return len(self.manage_FTPget())

InitializeClass(Event)

EventFactory = Factory(Event)
