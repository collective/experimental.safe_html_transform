from zope.interface import implements

from plone.behavior.interfaces import IBehavior

class BehaviorRegistration(object):
    implements(IBehavior)
    
    def __init__(self, title, description, interface, marker, factory):
        self.title = title
        self.description = description
        self.interface = interface
        self.marker = marker
        self.factory = factory
        
    def __repr__(self):
        return "<BehaviorRegistration for %s>" % (self.interface.__identifier__,)