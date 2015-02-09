"""
Interfaces for the unique id utility.

$Id: interfaces.py 107139 2009-12-27 06:03:02Z fafhrd $
"""
from zope.interface import Interface, Attribute, implements


class IIntIdsQuery(Interface):

    def getObject(uid):
        """Return an object by its unique id"""

    def getId(ob):
        """Get a unique id of an object.
        """

    def queryObject(uid, default=None):
        """Return an object by its unique id

        Return the default if the uid isn't registered
        """

    def queryId(ob, default=None):
        """Get a unique id of an object.

        Return the default if the object isn't registered
        """

    def __iter__():
        """Return an iteration on the ids"""


class IIntIdsSet(Interface):

    def register(ob):
        """Register an object and returns a unique id generated for it.

        The object *must* be adaptable to IKeyReference.

        If the object is already registered, its id is returned anyway.
        """

    def unregister(ob):
        """Remove the object from the indexes.

        KeyError is raised if ob is not registered previously.
        """

class IIntIdsManage(Interface):
    """Some methods used by the view."""

    def __len__():
        """Return the number of objects indexed."""

    def items():
        """Return a list of (id, object) pairs."""


class IIntIds(IIntIdsSet, IIntIdsQuery, IIntIdsManage):
    """A utility that assigns unique ids to objects.

    Allows to query object by id and id by object.
    """


class IIntIdEvent(Interface):
    """Generic base interface for IntId-related events"""

    object = Attribute("The object related to this event")

    original_event = Attribute("The ObjectEvent related to this event")


class IIntIdRemovedEvent(IIntIdEvent):
    """A unique id will be removed

    The event is published before the unique id is removed
    from the utility so that the indexing objects can unindex the object.
    """


class IntIdRemovedEvent(object):
    """The event which is published before the unique id is removed
    from the utility so that the catalogs can unindex the object.
    """

    implements(IIntIdRemovedEvent)

    def __init__(self, object, event):
        self.object = object
        self.original_event = event


class IIntIdAddedEvent(IIntIdEvent):
    """A unique id has been added

    The event gets sent when an object is registered in a
    unique id utility.
    """

    idmap = Attribute("The dictionary that holds an (utility -> id) mapping of created ids")


class IntIdAddedEvent(object):
    """The event which gets sent when an object is registered in a
    unique id utility.
    """

    implements(IIntIdAddedEvent)

    def __init__(self, object, event, idmap=None):
        self.object = object
        self.original_event = event
        self.idmap = idmap
