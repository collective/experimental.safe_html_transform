# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
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
$Id$
"""

import os, sys

# Load fixture
from Testing import ZopeTestCase
from Products.Marshall.tests.base import BaseTest

# Install our product
ZopeTestCase.installProduct('Marshall')
ZopeTestCase.installProduct('Archetypes')

from Products.CMFCore.utils import getToolByName
from Products.Marshall.predicates import add_predicate
from Products.Marshall.config import TOOL_ID as tool_id
from Products.Marshall import config
from Products.Marshall import registry


class PredicateTest(BaseTest):

    def afterSetUp(self):
        super(PredicateTest, self).afterSetUp()
        self.loginPortalOwner()
        registry.manage_addRegistry(self.portal)
        self.tool = getToolByName(self.portal, tool_id)

    def get(self, obj, **kw):
        return self.tool.getMarshallersFor(obj, **kw)

    def reverse(self):
        ids = self.tool.objectIds()
        for pos, id in enumerate(ids):
            self.tool.moveObjectToPosition(id, len(ids) - pos)

class DefaultPredicateTest(PredicateTest):

    def test_expression_filename(self):
        add_predicate(self.tool, id='doc',
                      title='.doc extension',
                      predicate='default',
                      expression="python: filename and filename.endswith('.doc')",
                      component_name='primary_field')
        add_predicate(self.tool, id='txt',
                      title='.txt extension',
                      predicate='default',
                      expression="python: filename and filename.endswith('.txt')",
                      component_name='rfc822')
        add_predicate(self.tool, id='default',
                      title='default',
                      predicate='default',
                      expression='',
                      component_name='primary_field')

        self.assertEquals(
            self.get(None, filename='sample.doc'), ('primary_field',))
        self.assertEquals(
            self.get(None, filename='sample.txt'),
            ('rfc822', 'primary_field'))

        # Make sure reordering the predicates does change the order
        # in which ids are returned.
        self.reverse()
        self.assertEquals(
            self.get(None, filename='sample.txt'),
            ('primary_field', 'rfc822'))

        self.assertEquals(self.get(None, filename='sample.rot'),
                          ('primary_field',))
        # Make sure it works even if no filename kw is passed in
        self.assertEquals(self.get(None), ('primary_field',))

    if config.hasLibxml2:
        def test_expression_content_type(self):
            add_predicate(
                self.tool, id='text_xml',
                title='text/xml content type',
                predicate='default',
                expression="python: content_type and content_type == 'text/xml'",
                component_name='simple_xml')
            add_predicate(
                self.tool,
                id='text_plain',
                title='text/plain content type',
                predicate='default',
                expression="python: content_type and content_type == 'text/plain'",
                component_name='rfc822')
            add_predicate(
                self.tool,
                id='default',
                title='default',
                predicate='default',
                expression="",
                component_name='primary_field')

            self.assertEquals(
                self.get(None, content_type='text/xml'),
                ('simple_xml', 'primary_field'))
            self.assertEquals(self.get(None, content_type='text/plain'),
                              ('rfc822', 'primary_field'))

            # Make sure reordering the predicates does change the order
            # in which ids are returned.
            self.reverse()
            self.assertEquals(self.get(None, content_type='text/plain'),
                              ('primary_field', 'rfc822'))

            # Make sure it works even if no content_type kw is passed in
            self.assertEquals(self.get(None), ('primary_field',))

    def test_expression_data(self):
        add_predicate(
            self.tool,
            id='data_len_3',
            title='data length > 3',
            predicate='default',
            expression="python: data and len(data) > 3",
            component_name='primary_field')
        add_predicate(
            self.tool,
            id='data_len_2',
            title='data length == 2',
            predicate='default',
            expression="python: data and len(data) == 2",
            component_name='rfc822')
        add_predicate(
            self.tool,
            id='default',
            title='default',
            predicate='default',
            expression='',
            component_name='primary_field')
        self.assertEquals(self.get(None, data='4242'), ('primary_field',))
        self.assertEquals(self.get(None, data='42'), ('rfc822', 'primary_field'))

        # Make sure reordering the predicates does change the order
        # in which ids are returned.
        self.reverse()
        self.assertEquals(self.get(None, data='42'), ('primary_field', 'rfc822'))

        # Make sure it works even if no data kw is passed in
        self.assertEquals(self.get(None), ('primary_field',))


class XMLNSPredicateTest(PredicateTest):

    def test_xmlns_element(self):
        p = add_predicate(
            self.tool,
            id='xmlns_attr',
            title='xmlns',
            predicate='xmlns_attr',
            expression='',
            component_name='primary_field')
        p.edit(element_name='test', value='FooBar')
        data = """<?xml version="1.0" encoding="UTF-8"?>
        <test>
           FooBar
        </test>
        """
        bad_data = """<?xml version="1.0" encoding="UTF-8"?>
        <test>
           FooBaz
        </test>
        """
        self.assertEquals(self.get(None, data=data), ('primary_field',))
        self.assertEquals(self.get(None, data=bad_data), ())
        self.assertEquals(self.get(None, data=''), ())

    def test_xmlns_element(self):
        p = add_predicate(
            self.tool,
            id='xmlns_attr',
            title='xmlns',
            predicate='xmlns_attr',
            expression='',
            component_name='primary_field')
        p.edit(element_name='test', value=None)
        data = """<?xml version="1.0" encoding="UTF-8"?>
        <test>
           Doesn't Matter
        </test>
        """
        self.assertEquals(self.get(None, data=data), ('primary_field',))

    def test_xmlns_element_ns(self):
        p = add_predicate(
            self.tool,
            id='xmlns_attr',
            title='xmlns',
            predicate='xmlns_attr',
            expression='',
            component_name='primary_field')
        p.edit(element_ns='http://foo.com/bar', element_name='test',
               value='FooBar')
        data = """<?xml version="1.0" encoding="UTF-8"?>
        <t:test xmlns:t="http://foo.com/bar">
                FooBar
        </t:test>
        """
        self.assertEquals(self.get(None, data=data), ('primary_field',))

    def test_xmlns_element_ns_att(self):
        p = add_predicate(
            self.tool,
            id='xmlns_attr',
            title='xmlns',
            predicate='xmlns_attr',
            expression='',
            component_name='primary_field')
        p.edit(element_ns='http://foo.com/bar', element_name='test',
               attr_name='wot', value='FooBar')
        data = """<?xml version="1.0" encoding="UTF-8"?>
        <t:test xmlns:t="http://foo.com/bar"
           wot="FooBar" />
        """
        self.assertEquals(self.get(None, data=data), ('primary_field',))

    def test_xmlns_element_ns_att_ns(self):
        p = add_predicate(
            self.tool,
            id='xmlns_attr',
            title='xmlns',
            predicate='xmlns_attr',
            expression='',
            component_name='primary_field')
        p.edit(element_ns='http://foo.com/bar', element_name='test',
               attr_ns='http://foo.com/bar', attr_name='wot',
               value='FooBar')
        data = """<?xml version="1.0" encoding="UTF-8"?>
        <t:test xmlns:t="http://foo.com/bar"
           t:wot="FooBar" />
        """
        self.assertEquals(self.get(None, data=data), ('primary_field',))


def test_suite():
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultPredicateTest))
    suite.addTest(unittest.makeSuite(XMLNSPredicateTest))
    return suite

