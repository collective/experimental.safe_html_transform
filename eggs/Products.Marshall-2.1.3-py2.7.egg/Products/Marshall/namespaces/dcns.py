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

from Products.CMFCore.utils import getToolByName
from Products.Marshall.handlers.atxml import XmlNamespace
from Products.Marshall.handlers.atxml import SchemaAttribute

RNGSchemaFragment = '''
  <define name="DublinCore"
          xmlns:dc="http://purl.org/dc/elements/1.1/"
          datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes"
          xmlns="http://relaxng.org/ns/structure/1.0">
    <choice>
      <zeroOrMore>
        <element name="dc:title"><text /></element>
      </zeroOrMore>
      <zeroOrMore>
        <element name="dc:description"><text /></element>
      </zeroOrMore>
      <zeroOrMore>
        <element name="dc:subject"><text /></element>
      </zeroOrMore>
      <zeroOrMore>
        <element name="dc:contributor"><data type="NMTOKEN" /></element>
      </zeroOrMore>
      <oneOrMore>
        <element name="dc:creator"><data type="NMTOKEN" /></element>
      </oneOrMore>
      <zeroOrMore>
        <element name="dc:language"><data type="language" /></element>
      </zeroOrMore>
      <zeroOrMore>
        <element name="dc:rights"><text /></element>
      </zeroOrMore>
    </choice>
  </define>
'''


class DCAttribute(SchemaAttribute):

    def __init__(self,
                 name,
                 accessor,
                 mutator,
                 many=False,
                 process=()):

        super(DCAttribute, self).__init__(name)

        self.accessor = accessor
        self.mutator = mutator
        self.many = many
        self.process = process

    def get(self, instance):
        accessor = getattr(instance, self.accessor)
        value = accessor()

        if not value:
            return None
        elif not isinstance(value, (list, tuple)):
            values = [value]
        elif self.many:
            values = value
        else:
            raise AssertionError("Many values on single value attr")

        return filter(None, values)

    def deserialize(self, instance, ns_data):

        value = ns_data.get(self.name)

        if not self.mutator or not value:
            return

        if self.process:
            for p in self.process:
                value = p(value)

        mutator = getattr(instance, self.mutator)
        mutator(value)

    def serialize(self, dom, parent_node, instance):
        values = self.get(instance)
        if not values:
            return False

        for value in values:
            elname = "%s:%s" % (self.namespace.prefix, self.name)
            node = dom.createElementNS(DublinCore.xmlns, elname)
            value_node = dom.createTextNode(str(value))
            node.appendChild(value_node)
            node.normalize()
            parent_node.appendChild(node)
        return True

    def processXmlValue(self, context, value):
        value = value and value.strip()
        if not value:
            return
        data = context.getDataFor(self.namespace.xmlns)

        if self.many:
            data.setdefault(self.name, []).append(value)
        else:
            data[self.name] = value


class normalizer(object):
    """ utility function ns """

    def space(text):
        return '\n'.join([s.strip() for s in text.splitlines()])
    space = staticmethod(space)

    def newline(text):
        return ' '.join([s.strip() for s in text.splitlines()])
    newline = staticmethod(newline)


class DublinCore(XmlNamespace):

    xmlns = 'http://purl.org/dc/elements/1.1/'
    prefix = 'dc'

    uses_at_fields = True

    attributes = (
        DCAttribute('title', 'Title', 'setTitle',
                    process=(normalizer.space, normalizer.newline)),

        DCAttribute('description', 'Description', 'setDescription',
                    process=(normalizer.space,)),

        DCAttribute('subject', 'Subject', 'setSubject', many=True),
        DCAttribute('contributor', 'Contributors', 'setContributors',
                    many=True),
        # this attr diverges from cmfdefault.dublincore
        DCAttribute('creator', 'Creators', 'setCreators', many=True),
        DCAttribute('rights', 'Rights', 'setRights'),
        DCAttribute('language', 'Language', 'setLanguage'))

    def getATFields(self):
        return ('title',
                'description',
                'contributors',
                'subject',
                'creators',
                'rights',
                'language')

    def getSchemaInfo(self):
        return [("DublinCore", "zeroOrMore", RNGSchemaFragment)]
