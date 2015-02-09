from zope.interface import implements
from zope.component import adapter
from zope.event import notify

from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent

from z3c.caching.interfaces import IPurgeable
from z3c.caching.interfaces import IPurgeEvent

class Purge(object):
    """Event implementation.
    
    To queue a purge for a given object, you can do::
    
        from plone.cachepurging import Purge
        from zope.event import notify
        
        notify(Purge(someobject))
    
    The actual URL(s) to purge are looked up via any relevant IPurgeURLs
    adapters.
    """
    
    implements(IPurgeEvent)
    
    def __init__(self, object):
        self.object = object


@adapter(IPurgeable, IObjectModifiedEvent)
def purgeOnModified(object, event):
    notify(Purge(object))

@adapter(IPurgeable, IObjectMovedEvent)
def purgeOnMovedOrRemoved(object, event):
    # Don't purge when added
    if event.oldName is not None and event.oldParent is not None:
        notify(Purge(object))
