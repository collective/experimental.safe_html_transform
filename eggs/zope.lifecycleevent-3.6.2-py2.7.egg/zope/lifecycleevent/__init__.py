##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Life cycle events
"""
__docformat__ = 'restructuredtext'

from zope.component.interfaces import ObjectEvent
from zope.interface import implements
from zope.event import notify

from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.lifecycleevent.interfaces import IAttributes
from zope.lifecycleevent.interfaces import ISequence


class ObjectCreatedEvent(ObjectEvent):
    """An object has been created"""

    implements(IObjectCreatedEvent)


class Attributes(object) :
    """
    Describes modified attributes of an interface.

        >>> from zope.lifecycleevent.interfaces import IObjectMovedEvent
        >>> desc = Attributes(IObjectMovedEvent, "newName", "newParent")
        >>> desc.interface == IObjectMovedEvent
        True
        >>> 'newName' in desc.attributes
        True
    """

    implements(IAttributes)

    def __init__(self, interface, *attributes) :
        self.interface = interface
        self.attributes = attributes


class Sequence(object) :
    """
    Describes modified keys of an interface.

        >>> from zope.container.interfaces import IContainer
        >>> desc = Sequence(IContainer, 'foo', 'bar')
        >>> desc.interface == IContainer
        True
        >>> desc.keys
        ('foo', 'bar')

    """

    implements(ISequence)

    def __init__(self, interface, *keys) :
        self.interface = interface
        self.keys = keys

class ObjectModifiedEvent(ObjectEvent):
    """An object has been modified"""

    implements(IObjectModifiedEvent)

    def __init__(self, object, *descriptions) :
        """
        Init with a list of modification descriptions.

        >>> from zope.interface import implements, Interface, Attribute
        >>> class ISample(Interface) :
        ...     field = Attribute("A test field")
        >>> class Sample(object) :
        ...     implements(ISample)

        >>> obj = Sample()
        >>> obj.field = 42
        >>> notify(ObjectModifiedEvent(obj, Attributes(ISample, "field")))

        """
        super(ObjectModifiedEvent, self).__init__(object)
        self.descriptions = descriptions


def modified(object, *descriptions):
    notify(ObjectModifiedEvent(object, *descriptions))


class ObjectCopiedEvent(ObjectCreatedEvent):
    """An object has been copied"""

    implements(IObjectCopiedEvent)

    def __init__(self, object, original):
        super(ObjectCopiedEvent, self).__init__(object)
        self.original = original

class ObjectMovedEvent(ObjectEvent):
    """An object has been moved"""

    implements(IObjectMovedEvent)

    def __init__(self, object, oldParent, oldName, newParent, newName):
        ObjectEvent.__init__(self, object)
        self.oldParent = oldParent
        self.oldName = oldName
        self.newParent = newParent
        self.newName = newName

class ObjectAddedEvent(ObjectMovedEvent):
    """An object has been added to a container"""

    implements(IObjectAddedEvent)

    def __init__(self, object, newParent=None, newName=None):
        if newParent is None:
            newParent = object.__parent__
        if newName is None:
            newName = object.__name__
        ObjectMovedEvent.__init__(self, object, None, None, newParent, newName)

class ObjectRemovedEvent(ObjectMovedEvent):
    """An object has been removed from a container"""

    implements(IObjectRemovedEvent)

    def __init__(self, object, oldParent=None, oldName=None):
        if oldParent is None:
            oldParent = object.__parent__
        if oldName is None:
            oldName = object.__name__
        ObjectMovedEvent.__init__(self, object, oldParent, oldName, None, None)

