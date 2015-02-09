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
import glob

# Load fixture
from Testing import ZopeTestCase
from Products.Marshall.tests.base import BaseTest

# Install our product
ZopeTestCase.installProduct('Marshall')
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('ATContentTypes')

from Products.CMFCore.utils import getToolByName
from Products.Marshall import registry
from Products.Marshall.registry import Registry, getRegisteredComponents
from Products.Marshall.registry import getComponent
from Products.Marshall.exceptions import MarshallingException
from Products.Marshall.tests import PACKAGE_HOME
from Products.Marshall.tests.examples import person
from Products.Marshall.tests.examples import blob
tool_id = Registry.id

def get_data(fname):
    return open(os.path.join(PACKAGE_HOME, 'data', fname), 'rb').read()

class MarshallerTest(BaseTest):

    def afterSetUp(self):
        super(MarshallerTest, self).afterSetUp()
        self.loginPortalOwner()
        registry.manage_addRegistry(self.portal)
        self.tool = getToolByName(self.portal, tool_id)
        self.infile = open(self.input, 'rb+')
        self.portal.invokeFactory(self.type_name, self.type_name.lower())
        self.obj = self.portal._getOb(self.type_name.lower())

    def beforeTearDown(self):
        super(MarshallerTest, self).beforeTearDown()
        self.infile.close()

    def test_marshall_roundtrip(self):
        marshaller = getComponent(self.prefix)
        content = self.infile.read()
        marshaller.demarshall(self.obj, content)
        ctype, length, got = marshaller.marshall(self.obj, filename=self.input)
        normalize = self.input.endswith('xml')

        self.assertEqualsDiff(content, got, normalize=normalize)

class ATXMLReferenceMarshallTest(BaseTest):

    def afterSetUp(self):
        super(ATXMLReferenceMarshallTest, self).afterSetUp()
        self.loginPortalOwner()
        registry.manage_addRegistry(self.portal)
        self.tool = getToolByName(self.portal, tool_id)
        self.marshaller = getComponent('atxml')

    def createPerson(self, ctx, id, **kw):
        person.addPerson(ctx, id, **kw)
        ob = ctx._getOb(id)
        ob.indexObject()
        return ob

    def test_uid_references(self):
        paulo = self.createPerson(
            self.portal,
            'paulo',
            title='Paulo da Silva')
        eligia = self.createPerson(
            self.portal,
            'eligia',
            title='Eligia M. da Silva')
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva')

        self.assertEquals(sidnei.getParents(), [])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <uid>
        %(uid)s
        </uid>
        </reference>
        </field>
        </metadata>
        """ % {'uid':paulo.UID()}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test a simple UID reference
        self.assertEquals(sidnei['parents'], [paulo.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <uid>
        XXX%(uid)sXXX
        </uid>
        </reference>
        </field>
        </metadata>
        """ % {'uid':paulo.UID()}
        # Test that invalid UID reference raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)


        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <uid>
        %(uid1)s
        </uid>
        </reference>
        </field>
        <field id="parents">
        <reference>
        <uid>
        %(uid2)s
        </uid>
        </reference>
        </field>
        </metadata>
        """ % {'uid1':paulo.UID(), 'uid2':eligia.UID()}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test that multiple UID references work.
        self.assertEquals(sidnei['parents'], [paulo.UID(), eligia.UID()])

        # *WARNING* the tests below are dependent on the one above.
        new_uid = '9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9'
        old_uid = paulo.UID()
        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <uid>
        %(uid)s
        </uid>
        </metadata>
        """ % {'uid':new_uid}
        self.marshaller.demarshall(paulo, ref_xml)
        # Test modifying a uid by marshalling
        self.assertEquals(paulo.UID(), new_uid)
        # Test that the references still apply
        self.assertEquals(sidnei['parents'], [paulo.UID(), eligia.UID()])
        # Test that trying to set a different object to the same UID
        # will raise an exception.
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

    def test_path_references(self):
        paulo = self.createPerson(
            self.portal,
            'paulo',
            title='Paulo da Silva')
        eligia = self.createPerson(
            self.portal,
            'eligia',
            title='Eligia M. da Silva')
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva')

        self.assertEquals(sidnei.getParents(), [])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <path>
        %(path)s
        </path>
        </reference>
        </field>
        </metadata>
        """ % {'path':'paulo'}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test a simple path reference
        self.assertEquals(sidnei['parents'], [paulo.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <path>
        XXX%(path)sXXX
        </path>
        </reference>
        </field>
        </metadata>
        """ % {'path':'paulo'}
        # Test that an invalid path reference raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <path>
        %(path1)s
        </path>
        </reference>
        </field>
        <field id="parents">
        <reference>
        <path>
        %(path2)s
        </path>
        </reference>
        </field>
        </metadata>
        """ % {'path1':'paulo', 'path2':'eligia'}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test multiple path references
        self.assertEquals(sidnei['parents'], [paulo.UID(), eligia.UID()])


    def test_metadata_references(self):
        paulo = self.createPerson(
            self.portal,
            'paulo',
            title='Paulo da Silva',
            description='Familia Silva')
        paulo_s = self.createPerson(
            self.portal,
            'paulo_s',
            title='Paulo Schuh',
            description='Familia Schuh')
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva',
            description='Familia Silva')

        self.assertEquals(sidnei.getParents(), [])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo Schuh
        </dc:title>
        <dc:description>
        Familia Schuh
        </dc:description>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test a simple metadata reference
        self.assertEquals(sidnei['parents'], [paulo_s.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Silva
        </dc:title>
        </metadata>
        </reference>
        </field>
        </metadata>
        """

        # Test that a metadata reference that doesn't uniquely
        # identifies a target raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Souza
        </dc:title>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        # Test that a metadata reference that doesn't uniquely
        # find at least one object raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo da Silva
        </dc:title>
        <dc:description>
        Familia Silva
        </dc:description>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test simple metadata reference
        self.assertEquals(sidnei['parents'], [paulo.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo da Silva
        </dc:title>
        <dc:description>
        Familia Silva
        </dc:description>
        </metadata>
        </reference>
        </field>
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo Schuh
        </dc:title>
        <dc:description>
        Familia Schuh
        </dc:description>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test multiple metadata references
        self.assertEquals(sidnei['parents'], [paulo.UID(), paulo_s.UID()])

    def test_linesfield(self):
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva',
            description='Familia Silva',
            food_preference='BBQ\nPizza\nShrimp')

        self.assertEquals(sidnei.getFoodPrefs(),
                          ('BBQ', 'Pizza', 'Shrimp'))

        lines_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="food_preference">
        BBQ
        </field>
        <field id="food_preference">
        Camaron Diablo
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, lines_xml)
        self.assertEquals(sidnei.getFoodPrefs(),
                          ('BBQ', 'Camaron Diablo'))
        ctype, length, got = self.marshaller.marshall(sidnei)
        expected = [s.strip() for s in """\
        <field id="food_preference">
        BBQ
        </field>
        <field id="food_preference">
        Camaron Diablo
        </field>""".splitlines()]
        got = [s.strip() for s in got.splitlines()]
        comp = [s for s in expected if s in got]
        self.assertEquals(comp, expected)

class BlobMarshallTest(BaseTest):

    def afterSetUp(self):
        super(BlobMarshallTest, self).afterSetUp()
        self.loginPortalOwner()
        registry.manage_addRegistry(self.portal)
        self.tool = getToolByName(self.portal, tool_id)
        self.marshaller = getComponent('atxml')

    def createBlob(self, ctx, id, **kw):
        blob.addBlob(ctx, id, **kw)
        ob = ctx._getOb(id)
        ob.indexObject()
        return ob

    def _test_blob_roundtrip(self, fname, data, mimetype, filename):
        blob = self.createBlob(self.portal, 'blob')

        field = blob.Schema()[fname]
        field.set(blob, data, mimetype=mimetype, filename=filename)

        # Marshall to XML
        ctype, length, got = self.marshaller.marshall(blob)

        # Populate from XML
        self.marshaller.demarshall(blob, got)

        # Marshall from XML again and compare to see if it's
        # unchanged.
        ctype, length, got2 = self.marshaller.marshall(blob)
        self.assertEqualsDiff(got, got2)

    def test_blob_image(self):
        data = get_data('image.gif')
        self._test_blob_roundtrip('aimage', data, 'image/gif', 'image.gif')

    def test_blob_file_text(self):
        data = get_data('file.txt')
        self._test_blob_roundtrip('afile', data, 'text/plain', 'file.txt')

    def test_blob_file_binary(self):
        data = get_data('file.pdf')
        self._test_blob_roundtrip('afile', data, 'application/pdf', 'file.pdf')

    def test_blob_file_html(self):
        data = get_data('file.html')
        self._test_blob_roundtrip('afile', data, 'text/html', 'file.html')

    def test_blob_text_text(self):
        data = get_data('file.txt')
        self._test_blob_roundtrip('atext', data, 'text/plain', 'file.txt')

    def test_blob_text_binary(self):
        data = get_data('file.pdf')
        self._test_blob_roundtrip('atext', data, 'application/pdf', 'file.pdf')

    def test_blob_text_html(self):
        data = get_data('file.html')
        self._test_blob_roundtrip('atext', data, 'text/html', 'file.html')

from zExceptions.ExceptionFormatter import format_exception
from ZPublisher.HTTPResponse import HTTPResponse

orig_exception = HTTPResponse.exception
def exception(self, **kw):
    def tag_search(*args):
        return False
    kw['tag_search'] = tag_search
    return orig_exception(self, **kw)

orig_setBody = HTTPResponse.setBody
def setBody(self, *args, **kw):
    kw['is_error'] = 0
    if len(args[0]) == 2:
        title, body = args[0]
        args = (body,) + args[1:]
    return orig_setBody(self, *args, **kw)

def _traceback(self, t, v, tb, as_html=1):
    return ''.join(format_exception(t, v, tb, as_html=as_html))

HTTPResponse._error_format = 'text/plain'
HTTPResponse._traceback = _traceback
HTTPResponse.exception = exception
HTTPResponse.setBody = setBody

class DocumentationTest(ZopeTestCase.Functional, BaseTest):

    def afterSetUp(self):
        super(DocumentationTest, self).afterSetUp()
        self.loginPortalOwner()
        registry.manage_addRegistry(self.portal)

def test_suite():
    import unittest
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    suite = unittest.TestSuite()

    suite.addTest(FunctionalDocFileSuite('doc/README.txt',
                                         package='Products.Marshall',
                                         test_class=DocumentationTest))

    # These tests depend on libxml2 being installed
    from Products.Marshall import config
    if not config.hasLibxml2:
        return suite


    ## XXX: reenable Blob and Image tests
    #suite.addTest(unittest.makeSuite(ATXMLReferenceMarshallTest))
    #suite.addTest(unittest.makeSuite(BlobMarshallTest))
    dirs = glob.glob(os.path.join(PACKAGE_HOME, 'input', '*'))
    comps = [i['name'] for i in getRegisteredComponents()]
    for d in dirs:
        prefix = os.path.basename(d)
        if prefix not in comps:
            continue
        files = glob.glob(os.path.join(d, '*'))
        for f in files:
            if os.path.isdir(f):
                continue
            f_name = os.path.basename(f)
            type_name = os.path.splitext(f_name)[0]
            k_dict = {'prefix':prefix,
                      'type_name':type_name,
                      'input':f}
            klass = type('%s%sTest' % (prefix, type_name),
                         (MarshallerTest,),
                         k_dict)
            suite.addTest(unittest.makeSuite(klass))
    return suite

