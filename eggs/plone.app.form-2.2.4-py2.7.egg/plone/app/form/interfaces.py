from zope.component.interfaces import IObjectEvent
from zope.formlib.interfaces import IPageForm
from zope.formlib.interfaces import ISubPageForm
from zope.interface import Interface, Attribute


class IPlonePageForm(IPageForm):
    """A page form with a couple extra attributes
    """
    description = Attribute("A longer description to display on the form")
    form_name = Attribute("A label to apply to the fieldset")

class IPloneSubPageForm(ISubPageForm):
    """A page form with a couple extra attributes
    """
    description = Attribute("A longer description to display on the form")
    form_name = Attribute("A label to apply to the fieldset")

class IEditForm(Interface):
    """Marker interface for edit forms. This allows things like the locking
    widget to be registered for edit forms only.
    """
    
class IEditBegunEvent(IObjectEvent):
    """An event signalling that editing has begun on an object
    """
    
class IEditFinishedEvent(IObjectEvent):
    """Base event signalling that an edit operation has completed
    """
    
class IEditCancelledEvent(IEditFinishedEvent):
    """An event signalling that editing was cancelled on the given object
    """
    
class IEditSavedEvent(IEditFinishedEvent):
    """An event signalling that editing was complated on the given object
    """
