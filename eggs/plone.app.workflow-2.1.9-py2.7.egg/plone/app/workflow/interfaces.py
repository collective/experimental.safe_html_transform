from zope.interface import Interface
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope import schema


class ILocalrolesModifiedEvent(IObjectModifiedEvent):
    """Interface for event which get fired after local roles of an object has
    been changed.
    """


class ISharingPageRole(Interface):
    """A named utility providing information about roles that are managed
    by the sharing page.

    Utility names should correspond to the role name.

    A user will be able to delegate the given role if a utility can be found
    and the user has the required_permission (or it's None).
    """

    title = schema.TextLine(title=u"A friendly name for the role")

    required_permission = schema.TextLine(
        title=u"Permission required to manage this local role",
        required=False)

    required_interface = schema.Object(
        schema=Interface,
        title=u"Context interface required to display this role",
        required=False)
