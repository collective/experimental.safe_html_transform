##################################################################
# Marshall: A framework for pluggable marshalling policies
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
Serialize CMF Framework Attributes - Type, Workflow,
Local Roles.

Created: 10/11/2004
Author: Kapil Thangavelu <k_vertigo@objectrealms.net>
$Id: $
"""

from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Marshall import config
from Products.Marshall.handlers.atxml import XmlNamespace
from Products.Marshall.handlers.atxml import SchemaAttribute
from Products.Marshall import utils

TypeRNGSchemaFragment = '''
  <define name="TypeInfo"
          xmlns:cmf="http://cmf.zope.org/namespaces/default"
          datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes"
          xmlns="http://relaxng.org/ns/structure/1.0">
           <element name="cmf:type">
             <text />
           </element>
          </zeroOrMore>
  </define>
'''


class TypeAttribute(SchemaAttribute):

    def getAttributeNames(self):
        return (self.name,)

    def get(self, instance):
        return instance.getPortalTypeName()

    def deserialize(self, instance, ns_data):
        value = ns_data.get(self.name)
        instance._setPortalTypeName(value)

    def serialize(self, dom, parent_node, instance):
        value = self.get(instance)
        elname = "%s:%s" % (self.namespace.prefix, self.name)
        node = dom.createElementNS(CMF.xmlns, elname)
        value_node = dom.createTextNode(str(value))
        node.appendChild(value_node)
        node.normalize()
        parent_node.appendChild(node)


SecurityRNGSchemaFragment = '''
  <define name="SecurityInfo"
          xmlns:zs="http://xml.zope.org/ns/local_roles"
          datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes"
          xmlns="http://relaxng.org/ns/structure/1.0">
          <zeroOrMore>
            <element name="zs:security">
              <zeroOrMore>
               <element name="zs:local_role">
                 <attribute name="user_id" />
                 <attribute name="role" />
               </element>
              </zeroOrMore>
            </element>
          </zeroOrMore>
  </define>
'''


class LocalRolesAttribute(SchemaAttribute):
    """
    serializes local roles into the form of

    <security>

      <local_role user_id="matz" role"bar" />
      <local_role user_id="john" role"manager" />
      <local_role user_id="john" role"owner" />
      <local_role user_id="mike" role"manager" />

    </security>

    """

    def getAttributeNames(self):
        return (self.name,)

    def get(self, instance):
        return getattr(instance, '__ac_local_roles__', {})

    def deserialize(self, instance, ns_data):
        values = ns_data.get(self.name)
        if not values:
            return
        for user_id, role in values:
            instance.manage_addLocalRoles(user_id, [role])

    def serialize(self, dom, parent_node, instance):
        values = self.get(instance)

        if not values:
            return

        elname = "%s:%s" % (self.namespace.prefix, "security")
        node = dom.createElementNS(CMF.xmlns, elname)

        for user_id, roles in values.items():
            for role in roles:
                elname = "%s:%s" % (self.namespace.prefix, self.name)
                lr_node = dom.createElementNS(CMF.xmlns, elname)
                user_attr = dom.createAttribute("user_id")
                user_attr.value = user_id
                lr_node.setAttributeNode(user_attr)

                role_attr = dom.createAttribute("role")
                role_attr.value = role
                lr_node.setAttributeNode(role_attr)
                node.appendChild(lr_node)

        parent_node.appendChild(node)

    def processXml(self, context, ctx_node):
        value = context.reader.Value()
        if value is None:
            return
        value = value.strip()
        if not value:
            return

        data = context.getDataFor(self.namespace.xmlns)
        values = data.setdefault(self.name, [])
        user_id = role = None

        while context.reader.MoveToNextAttribute():
            if context.reader.LocalName() == 'user_id':
                user_id = reader.Value()
            elif context.reader.LocalName() == 'role':
                role = context.reader.Value()

        assert user_id, role
        values.append((user_id, role))


WorkflowRNGSchemaFragment = '''
  <define name="WorkflowHistory"
          xmlns:cmf="http://cmf.zope.org/namespaces/default/"
          datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes"
          xmlns="http://relaxng.org/ns/structure/1.0">

      <element name="workflow_history">
       <oneOrMore>
        <element name="workflow">
          <attribute name="id" />
           <element name="history">
            <oneOrMore>
             <element name="wf_var">
              <attribute name="id" />
              <attribute name="type" />
              <attribute name="value" />
             </element>
            </oneOrMore>
           </element>
        </element>
       </oneOrMore>
      </element>

  </define>
'''


class WorkflowAttribute(SchemaAttribute):
    """
    serializes workflow state into the form below

    it will try to deal as best as possible with arbitrary
    python values, if it can't deal it will error out.

    <workflow_history>
      <workflow id="">
       <!-- in chronological order -->
       <history>
         <wf_var id="" type="" value="" />
         <wf_var id="" type="" value="" />
       </history>
      </workflow>
    </workflow_history>
    """

    def getAttributeNames(self):
        return ("workflow", "var", "history", 'workflow_history')

    def get(self, instance):
        return getattr(instance, 'workflow_history', None)

    def deserialize(self, instance, ns_data):
        wf_records = ns_data.get(self.name, {})
        wf_tool = getToolByName(instance, 'portal_workflow')

        for wf_id in wf_records:
            #history = list(instance.workflow_history.setdefault(wf_id, ()))
            history = []
            for record in wf_records[wf_id]:
                history.append(record)
            instance.workflow_history[wf_id] = tuple(history)

    def serialize(self, dom, parent_node, instance):
        history = self.get(instance)

        if history is None:
            return

        elname = "%s:workflow_history" % (self.namespace.prefix)
        node = dom.createElementNS(self.namespace.xmlns, elname)
        keys = history.keys()
        for wf_id in keys:
            wf_node = self.serializeWorkflow(dom, wf_id, history)
            node.appendChild(wf_node)
        parent_node.appendChild(node)

    def serializeWorkflow(self, dom, wf_id, wf_hist):

        prefix = self.namespace.prefix
        xmlns = self.namespace.xmlns

        elname = "%s:workflow" % prefix
        node = dom.createElementNS(xmlns, elname)

        wfid_attr = dom.createAttribute("id")
        wfid_attr.value = wf_id

        node.setAttributeNode(wfid_attr)

        for history in wf_hist[wf_id]:
            elname = "%s:%s" % (prefix, "history")
            history_node = dom.createElementNS(xmlns, elname)
            items = history.items()
            items.sort(lambda a, b: cmp(a[0], b[0]))

            for k, v in items:
                elname = "%s:%s" % (prefix, "var")
                var_node = dom.createElementNS(xmlns, elname)
                # Attributes normally do not have a namespace
                value_attr = dom.createAttribute("value")
                type_attr = dom.createAttribute("type")
                id_attr = dom.createAttribute("id")

                value, vtype = marshall_value(v)

                id_attr.value = str(k)
                type_attr.value = vtype
                value_attr.value = value

                var_node.setAttributeNode(id_attr)
                var_node.setAttributeNode(type_attr)
                var_node.setAttributeNode(value_attr)

                history_node.appendChild(var_node)

            node.appendChild(history_node)

        return node

    def processXml(self, context, node):

        tag, namespace = utils.fixtag(node.tag, context.ns_map)
        data = context.getDataFor(self.namespace.xmlns)
        nsprefix = node.tag[:node.tag.find('}') + 1]

        #iworkflow
        wf_node = node.find(nsprefix + 'workflow')
        wf_id = (wf_node.attrib.get(nsprefix + 'id') or
                 wf_node.attrib.get('id'))
                 #be tolerant with namespace sloppyness;)
        assert wf_id

        wf_data = data.setdefault(self.name, {})
        wf_data.setdefault(wf_id, [])
        wf_pstate = data.setdefault('_wf_pstate', wf_id)

        #history
        hist_nodes = wf_node.findall(nsprefix + 'history')
        wf_pstate = data['_wf_pstate']
        for hist_node in hist_nodes:
            record = {}
            data[self.name][wf_pstate].append(record)

            #var
            var_nodes = hist_node.findall(nsprefix + 'var')
            vid = vtype = value = None

            for var_node in var_nodes:
                vid = (var_node.attrib.get(nsprefix + 'id') or
                       var_node.attrib.get('id'))
                vtype = (var_node.attrib.get(nsprefix + 'type', None) or
                         var_node.attrib.get('type'))
                value = (var_node.attrib.get(nsprefix + 'value', None) or
                         var_node.attrib.get('value') or '')

                assert vid and vtype and not value is None

                value = demarshall_value(value, vtype)
                wf_pstate = data['_wf_pstate']
                data[self.name][wf_pstate][-1][vid] = value

        return True


def marshall_value(value):

    if isinstance(value, str):
        return value, 'str'
    elif isinstance(value, int):
        return str(value), 'int'
    elif isinstance(value, float):
        return str(value), 'float'
    elif isinstance(value, DateTime):
        return value.ISO8601(), 'date'
    elif isinstance(value, type(None)):
        return 'None', 'None'
    else:
        raise SyntaxError("Unknown value type %r" % value)


def demarshall_value(value, type):

    if type == 'str':
        return value
    elif type == 'int':
        return int(value)
    elif type == 'float':
        return float(value)
    elif type == 'date':
        if value.strip() == '':
            return None
        else:
            return DateTime(value)
    elif type == 'None':
        return None
    else:
        raise SyntaxError("Unknown Type %r" % type)


class CMF(XmlNamespace):

    xmlns = config.CMF_NS
    prefix = 'cmf'
    attributes = (
        TypeAttribute('type'),
        WorkflowAttribute('workflow_history '),
        LocalRolesAttribute('local_role'))

    def getAttributeByName(self, name):

        for attr in self.attributes:
            if name in attr.getAttributeNames():
                return attr

    def processXml(self, context, node):
        return XmlNamespace.processXml(self, context, node)

    def getSchemaInfo(self):

        return [
            ("TypeInfo", "optional", TypeRNGSchemaFragment),
            ("SecurityInfo", "optional", SecurityRNGSchemaFragment),
            ("WorkflowInfo", "optional", WorkflowRNGSchemaFragment)]
