##################################################################
# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004 EnfoldSystems, LLC
# Copyright (C) 2004 ObjectRealms, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################

"""
$Id: $
"""

# Georg Gogo. BERNHARD: UUencoded pluggable namespace for all at fields

#from DateTime import DateTime
from Products.Marshall.public import XmlNamespace, SchemaAttribute
from Products.Archetypes import public as atapi
from cStringIO import StringIO

import base64
import uu

DEBUG = False


class UUAttribute(SchemaAttribute):

#    def get(self, instance):
#        values = atapi.BaseObject.__getitem__(instance, self.name)
#
#        import pdb; pdb.set_trace() # @@@
#
#        field = instance.Schema().getField(self.name)
#        values = field.getRaw(instance)
#
#
#
#
#        if not isinstance(values, (list, tuple)):
#            values = [values]
#        return filter(None, values)

#    def get(self, instance):
#        values = atapi.BaseObject.__getitem__(instance, self.name)
#        if not isinstance(values, (list, tuple)):
#            values = [values]
#        return filter(None, values)

    def base64encode(self, string):
        return base64.encodestring(string)

    def base64decode(self, string):
        return base64.decodestring(string)

    def uuencode(self, string):
        # uu encode a srting
        stringio = StringIO()
        uu.encode(StringIO(string), stringio)
        return stringio.getvalue()

    def uudecode(self, string):
        # uu decode a srting
        stringio = StringIO()
        uu.decode(StringIO(string), stringio)
        return stringio.getvalue()

    def char_encode(self, string):
        return self.uuencode(string)

    def char_decode(self, string):
        return self.uudecode(string)

    def deserialize(self, instance, ns_data):
        values = ns_data.get(self.name)
        if not values:
            return

        field = instance.Schema().getField(self.name)
        baseunit = field.getBaseUnit(instance)
        isBinary = baseunit.isBinary()
        if isBinary:
            values = self.char_decode(values)

        mutator = instance.Schema()[self.name].getMutator(instance)
        if not mutator:
            #raise AttributeError("No Mutator for %s"%self.name)
            return

        mutator(values)

    def serialize(self, dom, parent_node, instance):

        if DEBUG:
            print "uuns/UUattribute", instance, self.name

        field = instance.Schema().getField(self.name)
        baseunit = field.getBaseUnit(instance)
        value = baseunit.getRaw(encoding=baseunit.original_encoding)

        isBinary = baseunit.isBinary()
        if isBinary:
            value = self.char_encode(value)

        elname = "%s:%s" % (self.namespace.prefix, self.name)
        node = dom.createElementNS(self.namespace.xmlns,
                                   elname)
        value_node = dom.createTextNode(value)
        node.appendChild(value_node)
        node.normalize()

        if  isBinary:
            id_attr = dom.createAttributeNS(self.namespace.xmlns, "binary")
            id_attr.value = "uuencoded"
            node.setAttributeNode(id_attr)

        parent_node.appendChild(node)


class UUNS(XmlNamespace):

    xmlns = 'uuns:ns:data'
    prefix = 'at_data'
    attributes = []

    #uses_at_fields = True

    def getAttributeByName(self, schema_name, context=None):
        if context is not None and schema_name not in self.at_fields:
            assert schema_name in context.instance.Schema()

        #if schema_name in self.at_fields:
        #    return self.at_fields[ schema_name ]

        attribute = UUAttribute(schema_name)
        attribute.setNamespace(self)

        return attribute

    def getAttributes(self, instance):

        field_keys = instance.Schema().keys()
        if DEBUG:
            print "UUNS/getAttributes", field_keys
        #import pdb; pdb.set_trace() # @@@
        #return fields

        # remove fields delegated to other namespaces
        #fields = []
        #for ns in getRegisteredNamespaces():
        #    if ns.uses_at_fields:
        #        fields.extend(ns.getATFields())
        #mset = Set(fields)
        #assert len(mset) == len(fields), "Multiple NS multiplexing field"
        #
        #field_keys = Set(instance.Schema().keys())-mset
        #
        ## remove primary field if still present
        #p = instance.getPrimaryField()
        #pk = p and p.getName() or None
        #if pk:
        #    field_keys.remove(pk)
        #

#        import pdb; pdb.set_trace() # @@@

        for fk in field_keys:
            field = instance.Schema().getField(fk)

            if hasattr(field, 'getBaseUnit'):
                baseunit = field.getBaseUnit(instance)
            else:
                #print ">>>>>>>> field==", field, "no getBaseUnit!"
                continue

            isBinary = baseunit.isBinary()

            if isBinary or instance.getPrimaryField() == field:
                yield self.getAttributeByName(fk)

            if DEBUG:
                print fk, isBinary

        #
        ## yield additional intrinsic at framework attrs
        #for attribute in self.at_fields.values():
        #    yield attribute

    def serialize(self, dom, parent_node, instance):
        for attribute in self.getAttributes(instance):
            attribute.serialize(dom, parent_node, instance)

    def deserialize(self, instance, ns_data):
        if not ns_data:
            return

        for attribute in self.getAttributes(instance):
            attribute.deserialize(instance, ns_data)
