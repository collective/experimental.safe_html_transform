#!/usr/bin/python
# -*- coding: utf-8 -*-

from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility

from z3c.relationfield.relation import RelationValue, _object

PATCHES = None


def get_from_object(self):
    if getattr(self, '_from_id', None):
        return _object(self._from_id)
    else:
        intids = getUtility(IIntIds)

        # Heya, is there no from_object? Please have a look at #12802

        self._from_id = intids.register(self.__dict__['from_object'])
        return _object(self._from_id)


def set_from_object(self, obj):
    if not obj:
        return
    intids = getUtility(IIntIds)
    self._from_id = intids.register(obj)


RelationValue.from_object = property(get_from_object, set_from_object)
