import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes import atapi
from Products.ATContentTypes.tests.utils import dcEdit

from Products.ATContentTypes.content.event import ATEvent
from Products.ATContentTypes.tests.utils import EmptyValidator
from Products.ATContentTypes.tests.utils import EmailValidator
from Products.ATContentTypes.tests.utils import URLValidator
from Products.ATContentTypes.tests.utils import NotRequiredTidyHTMLValidator
from DateTime import DateTime
from Products.ATContentTypes.interfaces import ICalendarSupport
from Products.ATContentTypes.interfaces import IATEvent
from zope.interface.verify import verifyObject


LOCATION = 'my location'
EV_TYPE = 'Meeting'
EV_URL = 'http://example.org/'
S_DATE = DateTime()
E_DATE = DateTime() + 1
C_NAME = 'John Doe'
C_PHONE = '+1212356789'
C_EMAIL = 'john@example.org'
EV_ATTENDEES = ('john@doe.com',
                'john@doe.org',
                'john@example.org')
TEXT = "lorem ipsum"


def editATCT(obj):
    dcEdit(obj)
    obj.setLocation(LOCATION)
    obj.setSubject(EV_TYPE)
    obj.setEventUrl(EV_URL)
    obj.setStartDate(S_DATE)
    obj.setEndDate(E_DATE)
    obj.setContactName(C_NAME)
    obj.setContactPhone(C_PHONE)
    obj.setContactEmail(C_EMAIL)
    obj.setAttendees(EV_ATTENDEES)
    obj.setText(TEXT)

tests = []


class TestSiteATEvent(atcttestcase.ATCTTypeTestCase):

    klass = ATEvent
    portal_type = 'Event'
    title = 'Event'
    meta_type = 'ATEvent'

    def test_doesImplementCalendarSupport(self):
        self.assertTrue(ICalendarSupport.providedBy(self._ATCT))
        self.assertTrue(verifyObject(ICalendarSupport, self._ATCT))

    def test_implementsATEvent(self):
        iface = IATEvent
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)
        self.assertEqual(new.start_date, new.start().asdatetime())
        self.assertEqual(new.end_date, new.end().asdatetime())
        self.assertEqual(new.start_date, S_DATE.asdatetime())
        self.assertEqual(new.end_date, E_DATE.asdatetime())
        self.assertEqual(new.duration, new.end_date - new.start_date)

    def test_cmp(self):
        e1 = self._ATCT
        e2 = self._createType(self.folder, self.portal_type, 'e2')
        day29 = DateTime('2004-12-29 0:00:00')
        day30 = DateTime('2004-12-30 0:00:00')
        day31 = DateTime('2004-12-31 0:00:00')

        e1.edit(startDate=day29, endDate=day30, title='event')
        e2.edit(startDate=day29, endDate=day30, title='event')
        self.assertEqual(cmp(e1, e2), 0)

        # start date
        e1.edit(startDate=day29, endDate=day30, title='event')
        e2.edit(startDate=day30, endDate=day31, title='event')
        self.assertEqual(cmp(e1, e2), -1)  # e1 < e2

        # duration
        e1.edit(startDate=day29, endDate=day30, title='event')
        e2.edit(startDate=day29, endDate=day31, title='event')
        self.assertEqual(cmp(e1, e2), -1)  # e1 < e2

        # title
        e1.edit(startDate=day29, endDate=day30, title='event')
        e2.edit(startDate=day29, endDate=day30, title='evenz')
        self.assertEqual(cmp(e1, e2), -1)  # e1 < e2

    def test_ical(self):
        event = self._ATCT
        event.setStartDate(DateTime('2001/01/01 12:00:00 GMT+1'))
        event.setEndDate(DateTime('2001/01/01 14:00:00 GMT+1'))
        event.setTitle('cool event')
        ical = event.getICal()
        lines = ical.split('\n')
        self.assertEqual(lines[0], "BEGIN:VEVENT")
        self.assertEqual(lines[5], "SUMMARY:%s" % event.Title())
        # times should be converted to UTC
        self.assertEqual(lines[6], "DTSTART:20010101T110000Z")
        self.assertEqual(lines[7], "DTEND:20010101T130000Z")

    def test_vcal(self):
        event = self._ATCT
        event.setStartDate(DateTime('2001/01/01 12:00:00 GMT+1'))
        event.setEndDate(DateTime('2001/01/01 14:00:00 GMT+1'))
        event.setTitle('cool event')
        vcal = event.getVCal()
        lines = vcal.split('\n')
        self.assertEqual(lines[0], "BEGIN:VEVENT")
        self.assertEqual(lines[7], "SUMMARY:%s" % event.Title())
        # times should be converted to UTC
        self.assertEqual(lines[1], "DTSTART:20010101T110000Z")
        self.assertEqual(lines[2], "DTEND:20010101T130000Z")

    def test_get_size(self):
        atct = self._ATCT
        editATCT(atct)
        self.assertEqual(atct.get_size(), len(TEXT))

tests.append(TestSiteATEvent)


class TestATEventFields(atcttestcase.ATCTFieldTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATEvent)

    def test_locationField(self):
        dummy = self._dummy
        field = dummy.getField('location')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getLocation',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setLocation',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission == ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'string', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == EmptyValidator,
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.StringWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_subjectField(self):
        dummy = self._dummy
        field = dummy.getField('subject')
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == (), 'Value is %s' % str(str(field.default)))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 1,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 1, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'Subject',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setSubject',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'mVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'lines', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.MetadataStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == EmptyValidator,
                        'Value is %s' % repr(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.KeywordWidget),
                        'Value is %s' % id(field.widget))

    def test_eventUrlField(self):
        dummy = self._dummy
        field = dummy.getField('eventUrl')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'event_url',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setEventUrl',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'string', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertEqual(field.validators, URLValidator)
        self.assertTrue(isinstance(field.widget, atapi.StringWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_startDateField(self):
        dummy = self._dummy
        field = dummy.getField('startDate')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 1, 'Value is %s' % field.required)
        self.assertTrue(field.default == None, 'Value is %s' % str(field.default))
        self.assertTrue(field.default_method == DateTime, 'Value is %s' % str(field.default_method))
        self.assertTrue(field.searchable == False, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'start',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setStartDate',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'datetime', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == (),
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.CalendarWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_endDateField(self):
        dummy = self._dummy
        field = dummy.getField('endDate')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 1, 'Value is %s' % field.required)
        self.assertTrue(field.default == None, 'Value is %s' % str(field.default))
        self.assertTrue(field.default_method == DateTime, 'Value is %s' % str(field.default_method))
        self.assertTrue(field.searchable == False, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'end',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setEndDate',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'datetime', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == (),
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.CalendarWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_contactNameField(self):
        dummy = self._dummy
        field = dummy.getField('contactName')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'contact_name',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setContactName',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'string', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == EmptyValidator,
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.StringWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_contactEmailField(self):
        dummy = self._dummy
        field = dummy.getField('contactEmail')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'contact_email',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setContactEmail',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'string', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == EmailValidator,
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.StringWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_contactPhoneField(self):
        dummy = self._dummy
        field = dummy.getField('contactPhone')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'contact_phone',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setContactPhone',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'string', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertEqual(field.validators, EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.StringWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_attendeesField(self):
        dummy = self._dummy
        field = dummy.getField('attendees')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == (), 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getAttendees',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setAttendees',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'lines', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(isinstance(field.widget, atapi.LinesWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

    def test_textField(self):
        dummy = self._dummy
        field = dummy.getField('text')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getText',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setText',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission ==
                        ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'text', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AnnotationStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AnnotationStorage(migrate=True),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == NotRequiredTidyHTMLValidator,
                        'Value is %s' % repr(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.RichWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

        self.assertTrue(field.primary == 1, 'Value is %s' % field.primary)
        self.assertTrue(field.default_content_type is None,
                        'Value is %s' % field.default_content_type)
        self.assertTrue(field.default_output_type == 'text/x-html-safe',
                        'Value is %s' % field.default_output_type)
        self.assertTrue('text/html' in field.getAllowedContentTypes(dummy))

    def beforeTearDown(self):
        # more
        atcttestcase.ATCTFieldTestCase.beforeTearDown(self)

tests.append(TestATEventFields)


class TestATEventFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'Event'
    views = ('event_view', 'vcs_view', 'ics_view', )

tests.append(TestATEventFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
