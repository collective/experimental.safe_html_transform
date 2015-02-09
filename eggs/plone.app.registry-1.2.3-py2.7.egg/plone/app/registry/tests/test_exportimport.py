import unittest2 as unittest
from plone.testing import zca

from StringIO import StringIO
from lxml import etree

from zope.interface import alsoProvides
from zope.component import provideUtility

from zope.configuration import xmlconfig

from plone.registry.interfaces import IRegistry, IInterfaceAwareRecord
from plone.registry.interfaces import IFieldRef
from plone.registry import Record, FieldRef, field

from plone.app.registry import Registry

from plone.app.registry.exportimport.handler import importRegistry, exportRegistry

from plone.supermodel.utils import prettyXML

from Products.GenericSetup.tests.common import DummyImportContext
from Products.GenericSetup.tests.common import DummyExportContext

from OFS.ObjectManager import ObjectManager

from plone.app.registry.tests import data

configuration = """\
<configure xmlns="http://namespaces.zope.org/zope">
    <include package="zope.component" file="meta.zcml" />
    <include package="plone.registry" />
    <include package="plone.app.registry.exportimport" file="handlers.zcml" />
</configure>
"""


class ExportImportTest(unittest.TestCase):

    layer = zca.UNIT_TESTING

    def setUp(self):
        self.site = ObjectManager('plone')
        self.registry = Registry('portal_registry')
        provideUtility(provides=IRegistry, component=self.registry)
        xmlconfig.xmlconfig(StringIO(configuration))

    def assertXmlEquals(self, expected, actual):

        expected_tree = etree.XML(expected)
        actual_tree = etree.XML(actual)

        if etree.tostring(expected_tree) != etree.tostring(actual_tree):
            print
            print "Expected:"
            print prettyXML(expected_tree)
            print

            print
            print "Actual:"
            print prettyXML(actual_tree)
            print

            raise AssertionError(u"XML mis-match")


class TestImport(ExportImportTest):

    def test_empty_import_no_purge(self):

        xml = "<registry/>"
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))

    def test_import_purge(self):

        xml = "<registry/>"
        context = DummyImportContext(self.site, purge=True)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(0, len(self.registry.records))

    def test_import_records(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(3, len(self.registry.records))

        self.failUnless('plone.app.registry.tests.data.ITestSettings.name' in self.registry)
        self.failUnless('plone.app.registry.tests.data.ITestSettings.age' in self.registry)

    def test_import_records_disallowed(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettingsDisallowed" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")

        try:
            importRegistry(context)
        except TypeError:
            pass
        else:
            self.fail()

    def test_import_records_omit(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettingsDisallowed">
        <omit>blob</omit>
    </records>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(3, len(self.registry.records))

        self.failUnless('plone.app.registry.tests.data.ITestSettingsDisallowed.name' in self.registry)
        self.failUnless('plone.app.registry.tests.data.ITestSettingsDisallowed.age' in self.registry)

    def test_import_records_remove(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}
        
        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))
        delete_xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" remove="true"/>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': delete_xml}
        
        importRegistry(context)

        self.assertEquals(0, len(self.registry.records))

    def test_import_records_delete_deprecated(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}
        
        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))
        delete_xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" delete="true"/>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': delete_xml}
        
        importRegistry(context)

        self.assertEquals(0, len(self.registry.records))

    def test_import_records_remove_with_omit(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}
        
        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))
        delete_xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" remove="true">
      <omit>name</omit>
    </records>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': delete_xml}
        
        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))

        self.failUnless('plone.app.registry.tests.data.ITestSettings.name' in self.registry)
        self.failIf('plone.app.registry.tests.data.ITestSettings.age' in self.registry)

    def test_import_records_remove_with_value(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}
        
        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))
        delete_xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" remove="true">
      <value key="name">Spam</value>
    </records>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': delete_xml}
        
        self.assertRaises(ValueError, importRegistry, context)

        self.assertEquals(2, len(self.registry.records))

    def test_import_records_with_prefix(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" prefix="plone.app.registry.tests.data.SomethingElse" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))

        self.failUnless('plone.app.registry.tests.data.SomethingElse.name' in self.registry)
        self.failUnless('plone.app.registry.tests.data.SomethingElse.age' in self.registry)

    def test_import_records_with_values(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" prefix="plone.app.registry.tests.data.SomethingElse">
        <value key="name">Magic</value>
        <value key="age">42</value>
    </records>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))

        self.failUnless('plone.app.registry.tests.data.SomethingElse.name' in self.registry)
        self.failUnless('plone.app.registry.tests.data.SomethingElse.age' in self.registry)

        self.assertEqual(self.registry['plone.app.registry.tests.data.SomethingElse.name'], 'Magic')
        self.assertEqual(self.registry['plone.app.registry.tests.data.SomethingElse.age'], 42)

    def test_import_value_only(self):
        xml = """\
<registry>
    <record name="test.export.simple">
        <value>Imported value</value>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(u"Simple record", self.registry.records['test.export.simple'].field.title)
        self.assertEquals(u"Imported value", self.registry['test.export.simple'])

    def test_import_interface_and_value(self):
        xml = """\
<registry>
    <record interface="plone.app.registry.tests.data.ITestSettingsDisallowed" field="age">
        <value>2</value>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(u"Age", self.registry.records['plone.app.registry.tests.data.ITestSettingsDisallowed.age'].field.title)
        self.assertEquals(2, self.registry['plone.app.registry.tests.data.ITestSettingsDisallowed.age'])

    def test_import_interface_with_differnet_name(self):
        xml = """\
<registry>
    <record name="plone.registry.oops" interface="plone.app.registry.tests.data.ITestSettingsDisallowed" field="age">
        <value>2</value>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(u"Age", self.registry.records['plone.registry.oops'].field.title)
        self.assertEquals(2, self.registry['plone.registry.oops'])

    def test_import_interface_no_value(self):
        xml = """\
<registry>
    <record interface="plone.app.registry.tests.data.ITestSettingsDisallowed" field="name" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(u"Name", self.registry.records['plone.app.registry.tests.data.ITestSettingsDisallowed.name'].field.title)
        self.assertEquals(u"Mr. Registry", self.registry['plone.app.registry.tests.data.ITestSettingsDisallowed.name'])

    def test_import_field_only(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <field type="plone.registry.field.TextLine">
          <default>N/A</default>
          <title>Simple record</title>
        </field>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.TextLine))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals(u"value", self.registry.records['test.registry.field'].field.__name__)
        self.assertEquals(u"N/A", self.registry['test.registry.field'])

    def test_import_field_ref(self):
        xml = """\
<registry>
    <record name="test.registry.field.override">
        <field ref="test.registry.field" />
        <value>Another value</value>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.registry.field'] = Record(
                field.TextLine(title=u"Simple record", default=u"N/A"),
                value=u"Sample value")

        importRegistry(context)

        self.assertEquals(2, len(self.registry.records))
        self.failUnless(IFieldRef.providedBy(self.registry.records['test.registry.field.override'].field))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field.override'].field.title)
        self.assertEquals(u"value", self.registry.records['test.registry.field.override'].field.__name__)
        self.assertEquals(u"Another value", self.registry['test.registry.field.override'])

    def test_import_field_and_interface(self):
        xml = """\
<registry>
    <record name="test.registry.field" interface="plone.app.registry.tests.data.ITestSettingsDisallowed" field="age">
        <field type="plone.registry.field.ASCIILine">
          <default>N/A</default>
          <title>Simple record</title>
        </field>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.ASCIILine))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals("N/A", self.registry['test.registry.field'])

    def test_import_overwrite_field_with_field(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <field type="plone.registry.field.ASCIILine">
          <default>Nada</default>
          <title>Simple record</title>
        </field>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Old value")

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.ASCIILine))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals("Nada", self.registry['test.registry.field'])

    def test_import_overwrite_field_with_interface(self):
        xml = """\
<registry>
    <record name="test.registry.field"  interface="plone.app.registry.tests.data.ITestSettingsDisallowed" field="age" />
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Old value")

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Int))
        self.assertEquals(u"Age", self.registry.records['test.registry.field'].field.title)
        self.assertEquals(None, self.registry['test.registry.field'])

    def test_import_collection_field(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <field type="plone.registry.field.FrozenSet">
          <title>Simple record</title>
          <default>
            <element>1</element>
            <element>3</element>
          </default>
          <value_type type="plone.registry.field.Int">
            <title>Value</title>
          </value_type>
        </field>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Old value")

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.FrozenSet))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals(frozenset([1, 3]), self.registry['test.registry.field'])

    def test_import_collection_value(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value>
            <element>4</element>
            <element>6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.Set(title=u"Simple record", value_type=field.Int(title=u"Val")),
                   value=set([1]))

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Set))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals(frozenset([4, 6]), self.registry['test.registry.field'])

    def test_import_collection_nopurge(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value purge="false">
            <element>4</element>
            <element>6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.Set(title=u"Simple record", value_type=field.Int(title=u"Val")),
                   value=set([1]))

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Set))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals(frozenset([1, 4, 6]), self.registry['test.registry.field'])

    def test_import_collection_list_append(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value purge="false">
            <element>4</element>
            <element>6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.List(title=u"Simple record", value_type=field.Int(title=u"Val")),
                   value=[2, 4])

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals([2, 4, 6], self.registry['test.registry.field'])

    def test_import_collection_tuple_append(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value purge="false">
            <element>b</element>
            <element>c</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.Tuple(title=u"Simple record", value_type=field.TextLine(title=u"Val")),
                   value=(u"a", u"b", ))

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals((u"a", u"b", u"c", ), self.registry['test.registry.field'])

    def test_import_collection_set_append(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value purge="false">
            <element>4</element>
            <element>6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.Set(title=u"Simple record", value_type=field.Int(title=u"Val")),
                   value=set([2, 4]))

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(set([2, 4, 6]), self.registry['test.registry.field'])

    def test_import_collection_frozenset_append(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value purge="false">
            <element>4</element>
            <element>6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.FrozenSet(title=u"Simple record", value_type=field.Int(title=u"Val")),
                   value=frozenset([2, 4]))

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(frozenset([2, 4, 6]), self.registry['test.registry.field'])

    def test_import_dict_field(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <field type="plone.registry.field.Dict">
          <title>Simple record</title>
          <default>
            <element key="a">1</element>
            <element key="b">3</element>
          </default>
          <key_type type="plone.registry.field.ASCIILine">
            <title>Key</title>
          </key_type>
          <value_type type="plone.registry.field.Int">
            <title>Value</title>
          </value_type>
        </field>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Old value")

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Dict))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals({'a': 1, 'b': 3}, self.registry['test.registry.field'])

    def test_import_dict_value(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value>
            <element key="x">4</element>
            <element key="y">6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.Dict(title=u"Simple record",
                              key_type=field.ASCIILine(title=u"Key"),
                              value_type=field.Int(title=u"Val")),
                   value={'a': 1})

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Dict))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals({'x': 4, 'y': 6}, self.registry['test.registry.field'])

    def test_import_dict_nopurge(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <value purge="false">
            <element key="x">4</element>
            <element key="y">6</element>
        </value>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.Dict(title=u"Simple record",
                              key_type=field.ASCIILine(title=u"Key"),
                              value_type=field.Int(title=u"Val")),
                   value={'a': 1})

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Dict))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals({'a': 1, 'x': 4, 'y': 6}, self.registry['test.registry.field'])

    def test_import_choice_field(self):
        xml = """\
<registry>
    <record name="test.registry.field">
        <field type="plone.registry.field.Choice">
          <title>Simple record</title>
          <values>
            <element>One</element>
            <element>Two</element>
          </values>
        </field>
    </record>
</registry>
"""

        self.registry.records['test.registry.field'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Old value")

        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.Choice))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals([u'One', u'Two'], [t.value for t in self.registry.records['test.registry.field'].field.vocabulary])
        self.assertEquals(None, self.registry['test.registry.field'])

    def test_import_with_comments(self):
        xml = """\
<registry>
    <records interface="plone.app.registry.tests.data.ITestSettings" prefix="plone.app.registry.tests.data.SomethingElse">
        <!-- set values in this interface -->
        <value key="name">Magic</value>
        <value key="age">42</value>
    </records>
    <record name="test.registry.field">
        <!-- comment on this field or value -->
        <field type="plone.registry.field.TextLine">
          <default>N/A</default>
          <!-- comment here too -->
          <title>Simple record</title>
        </field>
    </record>
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}
        
        importRegistry(context)

        self.assertEquals(3, len(self.registry.records))

        self.failUnless(isinstance(self.registry.records['test.registry.field'].field, field.TextLine))
        self.assertEquals(u"Simple record", self.registry.records['test.registry.field'].field.title)
        self.assertEquals(u"value", self.registry.records['test.registry.field'].field.__name__)
        self.assertEquals(u"N/A", self.registry['test.registry.field'])

        self.failUnless('plone.app.registry.tests.data.SomethingElse.name' in self.registry)
        self.failUnless('plone.app.registry.tests.data.SomethingElse.age' in self.registry)
        self.assertEqual(self.registry['plone.app.registry.tests.data.SomethingElse.name'], 'Magic')
        self.assertEqual(self.registry['plone.app.registry.tests.data.SomethingElse.age'], 42)


    def test_remove(self):
        xml = """\
<registry>
    <record name="test.export.simple" remove="true" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(0, len(self.registry.records))

    def test_delete_deprecated(self):
        xml = """\
<registry>
    <record name="test.export.simple" delete="true" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(0, len(self.registry.records))

    def test_delete_not_found(self):
        xml = """\
<registry>
    <record name="test.export.bogus" remove="true" />
</registry>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'registry.xml': xml}

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")
        importRegistry(context)

        self.assertEquals(1, len(self.registry.records))
        self.assertEquals(u"Simple record", self.registry.records['test.export.simple'].field.title)
        self.assertEquals(u"Sample value", self.registry['test.export.simple'])


class TestExport(ExportImportTest):

    def test_export_empty(self):

        xml = """<registry />"""
        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_simple(self):

        xml = """\
<registry>
  <record name="test.export.simple">
    <field type="plone.registry.field.TextLine">
      <default>N/A</default>
      <title>Simple record</title>
    </field>
    <value>Sample value</value>
  </record>
</registry>"""

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_with_interface(self):
        xml = """\
<registry>
  <record name="plone.app.registry.tests.data.ITestSettings.age" interface="plone.app.registry.tests.data.ITestSettings" field="age">
    <field type="plone.registry.field.Int">
      <min>0</min>
      <title>Age</title>
    </field>
    <value />
  </record>
  <record name="plone.app.registry.tests.data.ITestSettings.name" interface="plone.app.registry.tests.data.ITestSettings" field="name">
    <field type="plone.registry.field.TextLine">
      <default>Mr. Registry</default>
      <title>Name</title>
    </field>
    <value>Mr. Registry</value>
  </record>
  <record name="test.export.simple">
    <field type="plone.registry.field.TextLine">
      <default>N/A</default>
      <title>Simple record</title>
    </field>
    <value>Sample value</value>
  </record>
</registry>"""

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")

        self.registry.registerInterface(data.ITestSettings)

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_field_ref(self):

        xml = """\
<registry>
  <record name="test.export.simple">
    <field type="plone.registry.field.TextLine">
      <default>N/A</default>
      <title>Simple record</title>
    </field>
    <value>Sample value</value>
  </record>
  <record name="test.export.simple.override">
    <field ref="test.export.simple" />
    <value>Another value</value>
  </record>
</registry>"""

        self.registry.records['test.export.simple'] = refRecord = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"),
                   value=u"Sample value")

        self.registry.records['test.export.simple.override'] = \
            Record(FieldRef(refRecord.__name__, refRecord.field),
                   value=u"Another value")

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_with_collection(self):

        xml = """\
<registry>
  <record name="test.export.simple">
    <field type="plone.registry.field.List">
      <title>Simple record</title>
      <value_type type="plone.registry.field.Int">
        <title>Val</title>
      </value_type>
    </field>
    <value>
      <element>2</element>
    </value>
  </record>
</registry>"""
        self.registry.records['test.export.simple'] = \
            Record(field.List(title=u"Simple record", value_type=field.Int(title=u"Val")),
                   value=[2])

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_with_dict(self):

        xml = """\
<registry>
  <record name="test.export.dict">
    <field type="plone.registry.field.Dict">
      <default />
      <key_type type="plone.registry.field.ASCIILine">
        <title>Key</title>
      </key_type>
      <title>Dict</title>
      <value_type type="plone.registry.field.Int">
        <title>Value</title>
      </value_type>
    </field>
    <value>
      <element key="a">1</element>
    </value>
  </record>
</registry>"""

        self.registry.records['test.export.dict'] = \
            Record(field.Dict(title=u"Dict", default={},
                              key_type=field.ASCIILine(title=u"Key"),
                              value_type=field.Int(title=u"Value")),
                   value={'a': 1})

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_with_choice(self):

        xml = """\
<registry>
  <record name="test.export.choice">
    <field type="plone.registry.field.Choice">
      <title>Simple record</title>
      <vocabulary>dummy.vocab</vocabulary>
    </field>
    <value />
  </record>
</registry>"""

        self.registry.records['test.export.choice'] = \
            Record(field.Choice(title=u"Simple record", vocabulary=u"dummy.vocab"))

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])

    def test_export_with_missing_schema_does_not_error(self):

        xml = """\
<registry>
  <record name="test.export.simple" interface="non.existant.ISchema" field="blah">
    <field type="plone.registry.field.TextLine">
      <default>N/A</default>
      <title>Simple record</title>
    </field>
    <value>Sample value</value>
  </record>
</registry>"""

        self.registry.records['test.export.simple'] = \
            Record(field.TextLine(title=u"Simple record", default=u"N/A"), value=u"Sample value")

        # Note: These are nominally read-only!
        self.registry.records['test.export.simple'].field.interfaceName = 'non.existant.ISchema'
        self.registry.records['test.export.simple'].field.fieldName = 'blah'

        alsoProvides(self.registry.records['test.export.simple'], IInterfaceAwareRecord)

        context = DummyExportContext(self.site)
        exportRegistry(context)

        self.assertEquals('registry.xml', context._wrote[0][0])
        self.assertXmlEquals(xml, context._wrote[0][1])
