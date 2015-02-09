##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Unique id utility.

This utility assigns unique integer ids to objects and allows lookups
by object and by id.

This functionality can be used in cataloging.

$Id: __init__.py 100049 2009-05-17 17:53:56Z chrism $
"""
import random

import BTrees
from persistent import Persistent
from zope.component import adapter, getAllUtilitiesRegisteredFor, subscribers
from zope.event import notify
from zope.interface import implements
from zope.keyreference.interfaces import IKeyReference, NotYet
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.location.interfaces import ILocation
from zope.location.interfaces import IContained
from zope.security.proxy import removeSecurityProxy

from zope.intid.interfaces import IIntIds, IIntIdEvent
from zope.intid.interfaces import IntIdAddedEvent, IntIdRemovedEvent

class IntIds(Persistent):
    """This utility provides a two way mapping between objects and
    integer ids.

    IKeyReferences to objects are stored in the indexes.
    """
    implements(IIntIds, IContained)

    __parent__ = __name__ = None

    _v_nextid = None

    _randrange = random.randrange

    family = BTrees.family32

    def __init__(self, family=None):
        if family is not None:
            self.family = family
        self.ids = self.family.OI.BTree()
        self.refs = self.family.IO.BTree()

    def __len__(self):
        return len(self.ids)

    def items(self):
        return list(self.refs.items())

    def __iter__(self):
        return self.refs.iterkeys()

    def getObject(self, id):
        return self.refs[id]()

    def queryObject(self, id, default=None):
        r = self.refs.get(id)
        if r is not None:
            return r()
        return default

    def getId(self, ob):
        try:
            key = IKeyReference(ob)
        except (NotYet, TypeError):
            raise KeyError(ob)

        try:
            return self.ids[key]
        except KeyError:
            raise KeyError(ob)

    def queryId(self, ob, default=None):
        try:
            return self.getId(ob)
        except KeyError:
            return default

    def _generateId(self):
        """Generate an id which is not yet taken.

        This tries to allocate sequential ids so they fall into the
        same BTree bucket, and randomizes if it stumbles upon a
        used one.
        """
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(0, self.family.maxint)
            uid = self._v_nextid
            self._v_nextid += 1
            if uid not in self.refs:
                return uid
            self._v_nextid = None

    def register(self, ob):
        # Note that we'll still need to keep this proxy removal.
        ob = removeSecurityProxy(ob)
        key = IKeyReference(ob)

        if key in self.ids:
            return self.ids[key]
        uid = self._generateId()
        self.refs[uid] = key
        self.ids[key] = uid
        return uid

    def unregister(self, ob):
        # Note that we'll still need to keep this proxy removal.
        ob = removeSecurityProxy(ob)
        key = IKeyReference(ob, None)
        if key is None:
            return

        uid = self.ids[key]
        del self.refs[uid]
        del self.ids[key]


@adapter(ILocation, IObjectRemovedEvent)
def removeIntIdSubscriber(ob, event):
    """A subscriber to ObjectRemovedEvent

    Removes the unique ids registered for the object in all the unique
    id utilities.
    """
    utilities = tuple(getAllUtilitiesRegisteredFor(IIntIds))
    if utilities:
        key = IKeyReference(ob, None)
        # Register only objects that adapt to key reference
        if key is not None:
            # Notify the catalogs that this object is about to be removed.
            notify(IntIdRemovedEvent(ob, event))
            for utility in utilities:
                try:
                    utility.unregister(key)
                except KeyError:
                    pass

@adapter(ILocation, IObjectAddedEvent)
def addIntIdSubscriber(ob, event):
    """A subscriber to ObjectAddedEvent

    Registers the object added in all unique id utilities and fires
    an event for the catalogs.
    """
    utilities = tuple(getAllUtilitiesRegisteredFor(IIntIds))
    if utilities: # assert that there are any utilites
        key = IKeyReference(ob, None)
        # Register only objects that adapt to key reference
        if key is not None:
            idmap = {}
            for utility in utilities:
                idmap[utility] = utility.register(key)
            # Notify the catalogs that this object was added.
            notify(IntIdAddedEvent(ob, event, idmap))

@adapter(IIntIdEvent)
def intIdEventNotify(event):
    """Event subscriber to dispatch IntIdEvent to interested adapters."""
    adapters = subscribers((event.object, event), None)
    for adapter in adapters:
        pass # getting them does the work
