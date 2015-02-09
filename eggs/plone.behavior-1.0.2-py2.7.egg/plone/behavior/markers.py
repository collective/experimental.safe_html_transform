from zope.interface import alsoProvides
from plone.behavior.interfaces import IBehaviorAssignable

def applyMarkers(obj, event):
    """Event handler to apply markers for all behaviors enabled
    for the given type.
    """
    
    assignable = IBehaviorAssignable(obj, None)
    if assignable is None:
        return
        
    for behavior in assignable.enumerateBehaviors():
        if behavior.marker is not None:
            alsoProvides(obj, behavior.marker)
