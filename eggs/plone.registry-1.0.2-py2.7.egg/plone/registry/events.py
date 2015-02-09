from zope.interface import implements
from zope.component import subscribers, adapter

from plone.registry.interfaces import IRecordEvent
from plone.registry.interfaces import IRecordAddedEvent
from plone.registry.interfaces import IRecordRemovedEvent
from plone.registry.interfaces import IRecordModifiedEvent
from plone.registry.interfaces import IInterfaceAwareRecord

from plone.registry.recordsproxy import RecordsProxy

class RecordEvent(object):
    implements(IRecordEvent)

    def __init__(self, record):
        self.record = record

    def __repr__(self):
        return "<%s for %s>" % (self.__class__.__name__, self.record.__name__)

class RecordAddedEvent(RecordEvent):
    implements(IRecordAddedEvent)

class RecordRemovedEvent(RecordEvent):
    implements(IRecordRemovedEvent)

class RecordModifiedEvent(RecordEvent):
    implements(IRecordModifiedEvent)

    def __init__(self, record, oldValue, newValue):
        super(RecordModifiedEvent, self).__init__(record)
        self.oldValue = oldValue
        self.newValue = newValue

@adapter(IRecordEvent)
def redispatchInterfaceAwareRecordEvents(event):
    """When an interface-aware record received a record event,
    redispatch the event in a simlar manner to the IObjectEvent redispatcher.

    Note that this means one IRecordModifiedEvent will be fired for each
    change to a record.
    """

    record = event.record

    if not IInterfaceAwareRecord.providedBy(record):
        return

    schema = record.interface
    if schema is None:
        return

    proxy = RecordsProxy(record.__parent__, schema)

    adapters = subscribers((proxy, event), None)
    for adapter in adapters:
        pass # getting them does the work