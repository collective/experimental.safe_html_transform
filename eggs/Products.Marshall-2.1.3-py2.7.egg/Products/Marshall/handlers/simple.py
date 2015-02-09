# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004 Enfold Systems, LLC
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
#
"""
$Id: _xml.py 2994 2004-09-09 12:22:37Z dreamcatcher $
"""

import os
import thread
from types import ListType, TupleType
from xml.dom import minidom
from cStringIO import StringIO
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Marshall import Marshaller
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.config import REFERENCE_CATALOG, UUID_ATTR
from Products.Archetypes.debug import log
from Products.Marshall.config import AT_NS, CMF_NS, ATXML_SCHEMA
from Products.Marshall.exceptions import MarshallingException

import libxml2
libxml2.initParser()


class SimpleXMLMarshaller(Marshaller):

    __name__ = 'Simple XML Marshaller'

    def demarshall(self, instance, data, **kwargs):
        doc = libxml2.parseDoc(data)
        p = instance.getPrimaryField()
        pname = p and p.getName() or None
        try:
            fields = [f for f in instance.Schema().fields()
                      if f.getName() != pname]
            for f in fields:
                items = doc.xpathEval('/*/%s' % f.getName())
                if not len(items):
                    continue
                # Note that we ignore all but the first element if
                # we get more than one
                value = items[0].children
                if not value:
                    continue
                mutator = f.getMutator(instance)
                if mutator is not None:
                    mutator(value.content.strip())
        finally:
            doc.freeDoc()

    def marshall(self, instance, **kwargs):
        response = minidom.Document()
        doc = response.createElement(instance.portal_type.lower())
        response.appendChild(doc)

        p = instance.getPrimaryField()
        pname = p and p.getName() or None
        fields = [f for f in instance.Schema().fields()
                  if f.getName() != pname]

        for f in fields:
            value = instance[f.getName()]
            values = [value]
            if type(value) in [ListType, TupleType]:
                values = [str(v) for v in value]
            elm = response.createElement(f.getName())
            for value in values:
                value = response.createTextNode(str(value))
                elm.appendChild(value)
            doc.appendChild(elm)

        content_type = 'text/xml'
        data = response.toprettyxml().encode('utf-8')
        length = len(data)

        return (content_type, length, data)
