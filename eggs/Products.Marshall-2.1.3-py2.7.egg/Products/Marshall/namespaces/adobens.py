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

from DateTime import DateTime

from Products.Marshall.handlers.atxml import XmlNamespace
from Products.Marshall.handlers.atxml import SchemaAttribute


RNGSchemaFragment = '''
  <define name="DateInfo"
          xmlns:xmp="adobe:ns:meta"
          datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes"
          xmlns="http://relaxng.org/ns/structure/1.0">
        <zeroOrMore>
          <element name="xmp:CreateDate"><data type="dateTime" /></element>
        </zeroOrMore>
        <zeroOrMore>
          <element name="xmp:ModifyDate"><data type="dateTime" /></element>
        </zeroOrMore>
  </define>
'''


class XMPDate(SchemaAttribute):

    def get(self, instance):
        return getattr(instance, self.field_id)

    def deserialize(self, instance, ns_data):
        value = ns_data.get(self.name)
        if not value:
            return
        value = DateTime(value)
        setattr(instance, self.field_id, value)

    def serialize(self, dom, parent_node, instance):
        value = self.get(instance)
        if isinstance(value, DateTime):
            value = value.HTML4()
        elname = "%s:%s" % (self.namespace.prefix, self.name)
        node = dom.createElementNS(self.namespace.xmlns,
                                   elname)
        value_node = dom.createTextNode(value)
        node.appendChild(value_node)
        node.normalize()
        parent_node.appendChild(node)


class AdobeXMP(XmlNamespace):

    xmlns = 'adobe:ns:meta'
    prefix = 'xmp'

    uses_at_fields = True

    attributes = (
        XMPDate('CreateDate', 'creation_date'),
        XMPDate('ModifyDate', 'modification_date'),)

    def getATFields(self):
        return ('creation_date', 'modification_date')

    def getSchemaInfo(self):
        return (("DateInfo", "zeroOrMore", RNGSchemaFragment),)
