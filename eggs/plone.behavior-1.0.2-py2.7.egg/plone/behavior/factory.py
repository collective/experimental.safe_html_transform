from zope.interface import implements

from plone.behavior.interfaces import IBehaviorAdapterFactory
from plone.behavior.interfaces import IBehaviorAssignable

class BehaviorAdapterFactory(object):
    implements(IBehaviorAdapterFactory)
    
    def __init__(self, behavior):
        self.behavior = behavior
        
    def __call__(self, context):
        assignable = IBehaviorAssignable(context, None)
        if assignable is None:
            return None
        if not assignable.supports(self.behavior.interface):
            return None
        if self.behavior.factory is not None:
            adapted = self.behavior.factory(context)
        else:
            # When no factory is specified the object should provide the
            # behavior directly
            adapted = context
        return adapted
