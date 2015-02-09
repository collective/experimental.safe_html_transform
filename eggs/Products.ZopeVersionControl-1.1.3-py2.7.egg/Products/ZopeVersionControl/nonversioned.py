##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Support for non-versioned data embedded in versioned objects.

$Id: nonversioned.py 113728 2010-06-21 15:10:46Z ctheune $
"""

from Acquisition import aq_base
from OFS.ObjectManager import ObjectManager

from interfaces import INonVersionedData
from VersionSupport import isAVersionableResource
from zope.interface import implements


try:
    # Optional support for references.
    from Products.References.Proxy import proxyBase
    from Products.References.PathReference import PathReference
except ImportError:
    isProxyOrReference = None
else:
    def isProxyOrReference(obj):
        if proxyBase(obj) is not aq_base(obj):
            return 1
        if isinstance(obj, PathReference):
            return 1
        return 0


def getNonVersionedDataAdapter(obj):
    """Returns an INonVersionedData adapter for any object.

    This is a super-simplistic adapter implementation.
    """
    base = aq_base(obj)
    # If the object implements INonVersionedData, let it say
    # what its items are.
    if INonVersionedData.providedBy(base):
        return obj
    # If the object is an ObjectManager, use the ObjectManager adapter.
    if isinstance(base, ObjectManager):
        return ObjectManagerNonVersionedDataAdapter(obj)
    # Otherwise use the standard adapter.
    return StandardNonVersionedDataAdapter(obj)


def listNonVersionedObjects(obj):
    return getNonVersionedDataAdapter(obj).listNonVersionedObjects()

def getNonVersionedData(obj):
    return getNonVersionedDataAdapter(obj).getNonVersionedData()

def removeNonVersionedData(obj):
    getNonVersionedDataAdapter(obj).removeNonVersionedData()

def restoreNonVersionedData(obj, dict):
    getNonVersionedDataAdapter(obj).restoreNonVersionedData(dict)



class StandardNonVersionedDataAdapter:
    """Non-versioned data adapter for arbitrary things.
    """
    implements(INonVersionedData)

    def __init__(self, obj):
        self.obj = obj
        # __vc_ignore__, if set, is a tuple of attribute names to
        # manage independently of version control.
        self.attrs = getattr(obj, "__vc_ignore__", ())

    def listNonVersionedObjects(self):
        # Assume it's OK to clone all of the attributes.
        # They will be removed later by removeNonVersionedData.
        return ()

    def removeNonVersionedData(self):
        for attr in self.attrs:
            try:
                delattr(aq_base(self.obj), attr)
            except (AttributeError, KeyError):
                pass

    def getNonVersionedData(self):
        data = {}
        for attr in self.attrs:
            if hasattr( aq_base(self.obj), attr ):
                data[attr] = aq_base(getattr(aq_base(self.obj), attr))
        return data

    def restoreNonVersionedData(self, data):
        for attr in self.attrs:
            if data.has_key(attr):
                setattr(aq_base(self.obj), attr, data[attr])


class ObjectManagerNonVersionedDataAdapter(StandardNonVersionedDataAdapter):
    """Non-versioned data adapter for object managers.
    """
    implements(INonVersionedData)

    def listNonVersionedObjects(self):
        contents = self.getNonVersionedData()['contents']
        return contents.values()

    def removeNonVersionedData(self):
        StandardNonVersionedDataAdapter.removeNonVersionedData(self)
        obj = self.obj
        removed = {}
        contents = self.getNonVersionedData()['contents']
        for name, value in contents.items():
            obj._delOb(name)
            removed[name] = 1
        if obj._objects:
            obj._objects = tuple([info for info in obj._objects
                                  if not removed.has_key(info['id'])])

    def getNonVersionedData(self):
        contents = {}
        attributes = StandardNonVersionedDataAdapter.getNonVersionedData(self)
        for name, value in self.obj.objectItems():
            if not isAVersionableResource(value):
                # This object should include the state of subobjects
                # that won't be versioned independently.
                continue
            if isProxyOrReference is not None:
                if isProxyOrReference(value):
                    # This object should include the state of
                    # subobjects that are references.
                    continue
            contents[name] = aq_base(value)
        return {'contents': contents, 'attributes': attributes}

    def restoreNonVersionedData(self, data):
        StandardNonVersionedDataAdapter.restoreNonVersionedData(
            self, data['attributes'])
        # First build "ignore", a dictionary that lists which
        # items were stored in the repository.
        # Don't restore over those.
        obj = self.obj
        ignore = {}
        for name in obj.objectIds():
            ignore[name] = 1
        # Restore the items of the container.
        for name, value in data['contents'].items():
            if not ignore.has_key(name):
                obj._setOb(name, aq_base(value))
                if not hasattr(obj, '_tree'):
                    # Avoid generating events, since nothing was ever really
                    # removed or added.
                    obj._objects += ({'meta_type': value.meta_type,
                                      'id': name},)
                # If there is a _tree attribute, it's very likely
                # a BTreeFolder2, which doesn't need or want the
                # _objects attribute.
                # XXX This is a hackish way to check for BTreeFolder2s.
