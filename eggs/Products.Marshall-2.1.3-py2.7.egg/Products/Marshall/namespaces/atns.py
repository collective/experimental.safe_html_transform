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
from plone.uuid.interfaces import IUUID

"""
Serialize AT Schema Attributes

Created: 10/11/2004
Authors: Kapil Thangavelu <k_vertigo@objectrealms.net>
         Sidnei De Silva <sidnei@awkly.org>

$Id: $
"""
import re
from sets import Set

from Products.CMFCore.utils import getToolByName
from Products.Archetypes import config as atcfg
from Products.Archetypes.debug import log
from Products.Archetypes.interfaces import IBaseUnit
from Products.Archetypes.interfaces import IObjectField
from Products.Archetypes import public as atapi
from Products.Marshall import config
from Products.Marshall.handlers.atxml import XmlNamespace
from Products.Marshall.handlers.atxml import SchemaAttribute
from Products.Marshall.handlers.atxml import getRegisteredNamespaces
from Products.Marshall.exceptions import MarshallingException
from Products.Marshall import utils
from DateTime import DateTime
import transaction

_marker = object()


# Find control characters (0-31, 127) excluding:
#   9 (\t, tab)
#   10 (\n, new line character)
#   13 (\r, carriage return)
#   127 (\x1f, delete)
# which are handled properly by python xml libraries such
# as xml.dom.minidom and elementtree
CTRLCHARS_RE = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]')


def has_ctrlchars(value):
    if CTRLCHARS_RE.search(value):
        return True
    return False


class BoundReference(object):

    __slots__ = ('ns_data', 'attribute', 'instance')

    def __init__(self, ns_data, attribute, instance):
        self.ns_data = ns_data
        self.attribute = attribute
        self.instance = instance

    def resolve(self, context):
        self.attribute.deserialize(self.instance, self.ns_data)


class ATAttribute(SchemaAttribute):

    def get(self, instance):
        values = atapi.BaseObject.__getitem__(instance, self.name)
        if not isinstance(values, (list, tuple)):
            values = [values]
        return filter(None, values)

    def serialize(self, dom, parent_node, instance, options={}):

        encode_ctrlchars = options.get('encode_ctrlchars', True)

        values = self.get(instance)
        if not values:
            return

        for value in values:
            node = dom.createElementNS(self.namespace.xmlns, "field")
            name_attr = dom.createAttribute("name")
            name_attr.value = self.name
            node.setAttributeNode(name_attr)

            # try to get 'utf-8' encoded string
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            elif IBaseUnit.providedBy(value):
                value = value.getRaw(encoding='utf-8')
            else:
                value = str(value)

            if self.isReference(instance):
                if config.HANDLE_REFS:
                    ref_node = dom.createElementNS(self.namespace.xmlns,
                                                    'reference')
                    uid_node = dom.createElementNS(self.namespace.xmlns,
                                                    'uid')
                    value = dom.createTextNode(value)
                    uid_node.append(value)
                    ref_node.append(uid_node)
                    node.append(ref_node)
            elif (encode_ctrlchars and
                  isinstance(value, str) and
                  has_ctrlchars(value)):
                value = value.encode('base64')
                attr = dom.createAttributeNS(self.namespace.xmlns,
                                             'transfer_encoding')
                attr.value = 'base64'
                node.setAttributeNode(attr)
                value_node = dom.createCDATASection(value)
                node.appendChild(value_node)
            else:
                value_node = dom.createTextNode(value)
                node.appendChild(value_node)

            # set the mimetype if it is available
            field = instance.schema._fields[self.name]
            if IObjectField.providedBy(field):
                mime_attr = dom.createAttribute('mimetype')
                mime_attr.value = field.getContentType(instance)
                node.setAttributeNode(mime_attr)

            node.normalize()
            parent_node.appendChild(node)

        return True

    def processXmlValue(self, context, value):
        if value is None:
            return

        value = value.strip()
        if not value:
            return

        # decode node value if needed
        te = context.node.get('transfer_encoding', None)
        if te is not None:
            value = value.decode(te)

        context_data = context.getDataFor(self.namespace.xmlns)
        data = context_data.setdefault(self.name, {'mimetype': None})
        mimetype = context.node.get('mimetype', None)
        if mimetype is not None:
            data['mimetype'] = mimetype

        if data.has_key('value'):
            svalues = data['value']
            if not isinstance(svalues, list):
                data['value'] = svalues = [svalues]
            svalues.append(value)
            return
        else:
            data['value'] = value

    def deserialize(self, instance, ns_data, options={}):
        if not ns_data:
            return
        data = ns_data.get( self.name )
        if data is None:
            return
        values = data.get('value', None)
        if not values:
            return

	# check if we are a schema attribute
        if self.isReference( instance ):
            values = self.resolveReferences( instance, values)
            if not config.HANDLE_REFS :
                return

        field = instance.Schema()[self.name]
        mutator = field.getMutator(instance)
        if not mutator:
            # read only field no mutator, but try to set value still
            # since it might reflect object state (like ATCriteria)
            field = instance.getField( self.name ).set( instance, values )
            #raise AttributeError("No Mutator for %s"%self.name)
            return
        if self.name == "id":
            transaction.savepoint()

        if instance.getField(self.name).type == 'datetime':
            # make sure DateTime fields are constructed properly
            # by explicitly constructing a DateTime instance
            mutator(DateTime(values))
        else:
            mutator(values)

        # set mimetype if possible
        mimetype = data.get('mimetype', None)
        if (mimetype is not None and IObjectField.providedBy(field)):
            field.setContentType(instance, mimetype)

    def resolveReferences(self, instance, values):
        ref_values = []
        for value in values:
            if not isinstance(value, Reference):
                ref_values.append(value)
                continue
            ref = value.resolve(instance)
            if ref is None: #just for dup behavior
                raise MarshallingException(
                    "Could not resolve reference %r" % value)
            ref_values.append(ref)
        return ref_values

    def isReference(self, instance):
        return not not isinstance(instance.Schema()[self.name],
                                  atapi.ReferenceField)


class ReferenceAttribute(SchemaAttribute):

    __slots__ = ('reference', 'name')

    def __init__(self, name, reference):
        super(ReferenceAttribute, self).__init__(name)
        self.reference = reference

    def processXml(self, context, node):
        return True

    def processXmlValue(self, context, value):
        self.reference[self.name] = value.strip()


class ArchetypeUID(SchemaAttribute):

    def serialize(self, dom, parent_node, instance, options={}):
        value = IUUID(instance, '')
        node = dom.createElementNS(Archetypes.xmlns, "uid")
        nvalue = dom.createTextNode(value)
        node.appendChild(nvalue)
        parent_node.appendChild(node)

    def deserialize(self, instance, ns_data):
        values = ns_data.get(self.name)
        if not values:
            return
        self.resolveUID(instance, values)

    def resolveUID(self, instance, values):
        assert not isinstance(values, (list, tuple))
        at_uid = values
        #existing = getattr(instance, atcfg.UUID_ATTR, _marker)
        existing = IUUID(instance, _marker)
        if existing is _marker or existing != at_uid:
            ref = Reference(uid=at_uid)
            target = ref.resolve(instance)
            if target is not None:
                raise MarshallingException(
                        "Trying to set uid of "
                        "%s to an already existing uid "
                        "clashed with %s" % (
                        instance.absolute_url(), target.absolute_url()))
            instance._setUID(at_uid)


RNGSchemaFragment = '''
  <define name="ArchetypesFields"
          ns="http://plone.org/ns/archetypes/"
          xmlns:note="atxml:annotations"
          datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes"
          xmlns="http://relaxng.org/ns/structure/1.0">
    <element name="field">
      <note:info>
        All non-standard Archetypes fields are represented by a 'field'
        element, their id specified by an attribute 'id'.
      </note:info>
      <attribute name="id" />
      <choice>
        <text />
        <zeroOrMore>
          <element name="reference">
            <note:info>
              References can be made by UID (Archetypes),
              relative path, or by specifying a group of values
              that can uniquely identify a piece of content.
            </note:info>
            <choice>
              <zeroOrMore>
                <element name="uid"><text /></element>
              </zeroOrMore>
              <zeroOrMore>
                <element name="path"><text /></element>
              </zeroOrMore>
              <zeroOrMore>
                <ref name="Metadata" />
              </zeroOrMore>
            </choice>
          </element>
        </zeroOrMore>
      </choice>
    </element>
  </define>
  '''


class Archetypes(XmlNamespace):

    xmlns = config.AT_NS
    prefix = None
    attributes = []

    def __init__(self):
        super(Archetypes, self).__init__()
        self.last_schema_id = None
        self.in_reference_mode = False
        self.new_reference_p = True

        uid_attribute = ArchetypeUID('uid')
        uid_attribute.setNamespace(self)

        self.at_fields = {'uid': uid_attribute}

    def getAttributeByName(self, schema_name, context=None):
        if context is not None and schema_name not in self.at_fields:
            if not schema_name in context.instance.Schema():
                return
                raise AssertionError("invalid attribute %s" % (schema_name))

        if schema_name in self.at_fields:
            return self.at_fields[schema_name]

        attribute = ATAttribute(schema_name)
        attribute.setNamespace(self)

        return attribute

    def getAttributes(self, instance, exclude_attrs=()):

        # remove fields delegated to other namespaces
        fields = []
        for ns in getRegisteredNamespaces():
            if ns.uses_at_fields:
                fields.extend(ns.getATFields())
        assert len(Set(fields)) == len(fields), (
            "Multiple NS multiplexing field")

        field_keys = [k for k in instance.Schema().keys()
                      if k not in exclude_attrs and k not in fields]
        #Set(instance.Schema().keys())-mset

        # remove primary field if still present
        # XXX: we dont want to remove the PF, but want to be backward
        # XXX: compatible (how to do that best?)
        # p = instance.getPrimaryField()
        # pk = p and p.getName() or None
        # if pk and pk in field_keys:
        #     field_keys.remove( pk )

        for fk in field_keys:
            yield self.getAttributeByName(fk)

        # yield additional intrinsic at framework attrs
        for attribute in self.at_fields.values():
            yield attribute

    def serialize(self, dom, parent_node, instance, options):

        exclude_attrs = options.get('atns_exclude', ())

        for attribute in self.getAttributes(instance, exclude_attrs):
            if (hasattr(attribute, 'isReference') and
                attribute.isReference(instance)):
                continue
            attribute.serialize(dom, parent_node, instance, options)

    def deserialize(self, instance, ns_data, options):
        if not ns_data:
            return

        for attribute in self.getAttributes(instance):
            if (not config.HANDLE_REFS and
                hasattr(attribute, 'isReference') and
                attribute.isReference(instance)):
                # simply skip it then... Gogo
                continue
            attribute.deserialize(instance, ns_data)

    def processXml(self, context, data_node):

        tagname, namespace = utils.fixtag(data_node.tag, context.ns_map)

        if tagname == 'metadata':
            # ignore the container
            return False

        elif tagname == 'reference':
            # switch to reference mode, we tell the parser that we want
            # to explictly recieve all new node parse events, so we
            # can introspect the nested metadata that can be used
            # in reference specification.
            self.in_reference_mode = True
            self.new_reference_p = True
            assert self.last_schema_id
            context.setNamespaceDelegate(self)
            return False

        elif tagname == 'field':
            # basic at field specified, find the matching attribute
            # and annotate the data node with it
            schema_name = data_node.attrib.get('name', None)
            if schema_name is None:
                log("'id' attribute for at:field is deprecated, "
                    "use 'name' instead")
                schema_name = data_node.attrib.get('id')
            assert schema_name, "No field name specified in at:field element"
            #print "field", schema_name
            self.last_schema_id = schema_name
            attribute = self.getAttributeByName(schema_name, context)
            if attribute is None:
                #print "na", schema_name
                return False
            data_node.set('attribute', attribute)
            return True

        elif self.in_reference_mode:
            # if we get new metadata elements while in references, they
            # are stored as additional data for resolving the reference
            # latter.
            data = context.getDataFor(self.xmlns)
            srefs = data.setdefault(self.last_schema_id, [])

            # if we've already added a reference to the node data,
            # put additional reference specification data onto the
            # existing reference.
            if self.new_reference_p:
                ref = Reference()
                srefs.append(ref)
                self.new_reference_p = False
            else:
                ref = srefs[-1]

            attribute = ReferenceAttribute(data_node.name, ref)
            data_node.set('attribute', attribute)
            return True

        elif tagname in self.at_fields:
            # pseudo fields like uid which are specified in a custom manner
            attribute = self.getAttributeByName(tagname)
            if attribute is None:
                return False
            data_node.set('attribute', attribute)
            return True

        return False

    def processXmlEnd(self, name, context):
        if name == 'reference':
            context.setNamespaceDelegate(None)
            self.in_reference_mode = False
            self.last_schema_id = None # guard against bad xml

    def getSchemaInfo(self):
        return [("ArchetypesFields", "zeroOrMore", RNGSchemaFragment)]


class Reference(dict):

    index_map = dict([('title', 'Title'),
                      ('description', 'Description'),
                      ('creation_date', 'created'),
                      ('modification_data', 'modified'),
                      ('creators', 'Creator'),
                      ('subject', 'Subject'),
                      ('effectiveDate', 'effective'),
                      ('expirationDate', 'expires'),
                      ])

    def resolve(self, context):
        uid = self.get('uid')
        if uid is not None:
            rt = getToolByName(context, atcfg.REFERENCE_CATALOG)
            return rt.lookupObject(uid)
        path = self.get('path')
        if path is not None:
            return context.restrictedTraverse(path, None)
        catalog = getToolByName(context, 'portal_catalog')
        params = [(k, v) for k, v in self.items() \
                  if k not in ('uid', 'path')]
        kw = [(self.index_map.get(k), v) for k, v in params]
        kw = dict(filter(lambda x: x[0] is not None and x, kw))
        res = catalog(**kw)
        if not res:
            return None

        # First step: Try to filter by brain metadata
        # *Usually* a metadata item will exist with the same name
        # as the index.
        verify = lambda obj: filter(None, [obj[k] == v for k, v in kw.items()])
        for r in res:
            # Shortest path: If a match is found, return immediately
            # instead of checking all of the results.
            if verify(r):
                return r.getObject()

        # Second step: Try to get the real objects and look
        # into them. Should be *very* slow, so use with care.
        # We use __getitem__ to access the field raw data.
        verify = lambda obj: filter(None, [obj[k] == v for k, v in params])
        valid = filter(verify, [r.getObject() for r in res])
        if not valid:
            return None
        if len(valid) > 1:
            raise MarshallingException('Metadata reference does not '
                                       'uniquely identifies the reference.')
        return valid[0]
