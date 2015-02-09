##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""Dublin Core Annotatable Adapter
"""
__docformat__ = 'restructuredtext'

from persistent.dict import PersistentDict

from zope.annotation.interfaces import IAnnotatable
from zope.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.interface import implements
from zope.location import Location
from zope.dublincore.interfaces import IWriteZopeDublinCore
from zope.dublincore.zopedublincore import DateProperty
from zope.dublincore.zopedublincore import ScalarProperty
from zope.dublincore.zopedublincore import ZopeDublinCore

DCkey = "zope.app.dublincore.ZopeDublinCore"


class ZDCAnnotatableAdapter(ZopeDublinCore, Location):
    """Adapt annotatable objects to Zope Dublin Core."""
    implements(IWriteZopeDublinCore)
    adapts(IAnnotatable)

    annotations = None

    def __init__(self, context):
        annotations = IAnnotations(context)
        dcdata = annotations.get(DCkey)
        if dcdata is None:
            self.annotations = annotations
            dcdata = ZDCAnnotationData()

        super(ZDCAnnotatableAdapter, self).__init__(dcdata)

    def _changed(self):
        if self.annotations is not None:
            self.annotations[DCkey] = self._mapping
            self.annotations = None


class ZDCAnnotationData(PersistentDict):
    """Data for a Dublin Core annotation.

    A specialized class is used to allow an alternate fssync
    serialization to be registered.  See the
    zope.dublincore.fssync package.
    """


# Hybrid adapters.
#
# Adapter factories created using this support the Dublin Core using a
# mixture of annotations and data on the context object.


class DirectProperty(object):

    def __init__(self, name, attrname):
        self.__name__ = name
        self.__attrname = attrname

    def __get__(self, inst, klass):
        if inst is None:
            return self
        context = inst._ZDCPartialAnnotatableAdapter__context
        return getattr(context, self.__attrname, u"")

    def __set__(self, inst, value):
        if not isinstance(value, unicode):
            raise TypeError("Element must be unicode")
        context = inst._ZDCPartialAnnotatableAdapter__context
        oldvalue = getattr(context, self.__attrname, None)
        if oldvalue != value:
            setattr(context, self.__attrname, value)

def partialAnnotatableAdapterFactory(direct_fields):
    if not direct_fields:
        raise ValueError("only use partialAnnotatableAdapterFactory()"
                         " if at least one DC field is implemented directly")
    fieldmap = {}
    try:
        # is direct_fields a sequence or a mapping?
        direct_fields[0]
    except KeyError:
        # direct_fields: { dc_name: attribute_name }
        fieldmap.update(direct_fields)
    else:
        for attrname in direct_fields:
            fieldmap[attrname] = attrname

    class ZDCPartialAnnotatableAdapter(ZDCAnnotatableAdapter):

        def __init__(self, context):
            self.__context = context
            # can't use super() since this isn't a globally available class
            ZDCAnnotatableAdapter.__init__(self, context)

    for dcname, attrname in fieldmap.iteritems():
        oldprop = ZopeDublinCore.__dict__.get(dcname)
        if oldprop is None:
            raise ValueError("%r is not a valid DC field" % dcname)
        if (isinstance(oldprop, DateProperty)
            or not isinstance(oldprop, ScalarProperty)):
            raise ValueError("%r is not a supported DC field" % dcname)
        prop = DirectProperty(dcname, attrname)
        setattr(ZDCPartialAnnotatableAdapter, dcname, prop)

    return ZDCPartialAnnotatableAdapter
