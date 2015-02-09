from zope.interface import implementer
from zope.lifecycleevent import ObjectModifiedEvent
from plone.app.workflow.interfaces import ILocalrolesModifiedEvent


@implementer(ILocalrolesModifiedEvent)
class LocalrolesModifiedEvent(ObjectModifiedEvent):
    """Gets fired after local roles of an object has been changed.
    """
