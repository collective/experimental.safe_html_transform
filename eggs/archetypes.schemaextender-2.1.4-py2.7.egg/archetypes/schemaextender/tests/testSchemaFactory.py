import unittest
from archetypes.schemaextender.extender import instanceSchemaFactory
from archetypes.schemaextender.tests.case import TestCase
from archetypes.schemaextender.tests.mocks import Extender
from archetypes.schemaextender.tests.mocks import OrderableExtender
from archetypes.schemaextender.tests.mocks import MockField


class NonExtenderTests(TestCase):

    def testNoExtenderMeansNoChanges(self):
        schema=instanceSchemaFactory(self.instance)
        self.assertTrue(schema is self.instance.schema)


class ExtenderTests(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.provideAdapter(Extender, name=u"atse.tests.extender")
        Extender.fields=[]

    def testNopExtender(self):
        schema=instanceSchemaFactory(self.instance)
        self.assertEqual(schema.signature(), self.instance.schema.signature())

    def testExtendWithSingleField(self):
        Extender.fields=[MockField()]
        schema=instanceSchemaFactory(self.instance)
        self.assertTrue("MockField" in schema)

    def testExtendTwiceCreateOnce(self):
        Extender.fields=[MockField(), MockField()]
        schema=instanceSchemaFactory(self.instance)
        self.assertEqual(schema.keys().count("MockField"), 1)


class OrderableExtenderTests(ExtenderTests):

    def setUp(self):
        TestCase.setUp(self)
        self.provideAdapter(OrderableExtender, name=u"atse.tests.extender")
        Extender.fields=[]

    def testFieldOrder(self):
        Extender.fields=[MockField()]
        schema=instanceSchemaFactory(self.instance)
        order=[f.getName() for f in schema.getSchemataFields("default")]
        self.assertEqual(order[0], "MockField")


def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NonExtenderTests))
    suite.addTest(unittest.makeSuite(ExtenderTests))
    suite.addTest(unittest.makeSuite(OrderableExtenderTests))
    return suite
