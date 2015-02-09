import unittest
from Products.Archetypes.public import Schema
from Products.Archetypes.public import ManagedSchema
from Products.Archetypes.utils import OrderedDict
from archetypes.schemaextender.extender import get_schema_order
from archetypes.schemaextender.extender import set_schema_order
from archetypes.schemaextender.tests.mocks import MockField


class GetSchemaOrderTests(unittest.TestCase):

    def testEmptySchema(self):
        schema=Schema()
        self.assertEqual(get_schema_order(schema), {})

    def testSchemataOrdering(self):
        schema=ManagedSchema()
        schema.addField(MockField("one", "one"))
        schema.addField(MockField("two", "two"))
        order=get_schema_order(schema)
        self.assertEqual(order, {"two": ["two"], "one": ["one"]})
        self.assertEqual(order.keys(), ["one", "two"])

        schema.moveSchemata("two", -1)
        order=get_schema_order(schema)
        self.assertEqual(order, {"two": ["two"], "one": ["one"]})
        self.assertEqual(order.keys(), ["two", "one"])

    def testFieldOrdering(self):
        schema=Schema()
        schema.addField(MockField("one"))
        schema.addField(MockField("two"))
        order=get_schema_order(schema)
        self.assertEqual(order, {"default": ["one", "two"]})

        schema.moveField("one", 1)
        order=get_schema_order(schema)
        self.assertEqual(order, {"default": ["two", "one"]})


class SetSchemaOrderTests(unittest.TestCase):

    def testEmptySchema(self):
        schema=Schema()
        before=schema.signature()
        set_schema_order(schema, {})
        self.assertEqual(schema.signature(), before)

    def testNopReorderErrors(self):
        schema=Schema()
        schema.addField(MockField("one"))
        schema.addField(MockField("two"))
        self.assertRaises(ValueError, set_schema_order, schema, {})

    def testIdentityFieldReorder(self):
        schema=Schema()
        schema.addField(MockField("one"))
        schema.addField(MockField("two"))
        set_schema_order(schema, {"default": ["one", "two"]})
        self.assertEqual(schema._names, ["one", "two"])

    def testSwapTwoFields(self):
        schema=Schema()
        schema.addField(MockField("one"))
        schema.addField(MockField("two"))
        set_schema_order(schema, {"default": ["two", "one"]})
        self.assertEqual(schema._names, ["two", "one"])

    def testIdentitySchemataReorder(self):
        schema=ManagedSchema()
        schema.addField(MockField("one", "one"))
        schema.addField(MockField("two", "two"))
        command=OrderedDict()
        command["one"]=["one"]
        command["two"]=["two"]
        set_schema_order(schema, command)
        self.assertEqual(schema.getSchemataNames(), ["one", "two"])

    def testSwapTwoSchemata(self):
        schema=ManagedSchema()
        schema.addField(MockField("one", "one"))
        schema.addField(MockField("two", "two"))
        command=OrderedDict()
        command["two"]=["two"]
        command["one"]=["one"]
        set_schema_order(schema, command)
        self.assertEqual(schema.getSchemataNames(), ["two", "one"])

    def testMoveFieldToOtherSchemata(self):
        schema=ManagedSchema()
        schema.addField(MockField("one", "one"))
        schema.addField(MockField("two", "two"))
        set_schema_order(schema, {"one": ["one", "two"]})
        self.assertEqual(schema.getSchemataNames(), ["one"])
        self.assertEqual(schema._names, ["one", "two"])


def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GetSchemaOrderTests))
    suite.addTest(unittest.makeSuite(SetSchemaOrderTests))
    return suite
