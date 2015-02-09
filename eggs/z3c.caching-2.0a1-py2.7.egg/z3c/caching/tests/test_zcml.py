from unittest import TestCase

from zope.component import provideAdapter
from zope.configuration import xmlconfig

from z3c.caching.registry import getGlobalRulesetRegistry
from z3c.caching.registry import RulesetRegistry

from z3c.caching.tests.test_registry import TestView

import zope.component.testing
import z3c.caching.tests

class TestZCMLDeclarations(TestCase):

    def setUp(self):
        provideAdapter(RulesetRegistry)
        self.registry = getGlobalRulesetRegistry()
    
    def tearDown(self):
        self.registry.clear()
        zope.component.testing.tearDown()

    def test_simple_registration(self):
        i = TestView()
        self.failUnless(self.registry[i] is None)
        
        zcml = xmlconfig.XMLConfig("test1.zcml", z3c.caching.tests)
        zcml()
        
        i = TestView()
        self.assertEqual(self.registry[i], "first")

    def test_conflicting_registrations(self):
        zcml = xmlconfig.XMLConfig("test2.zcml", z3c.caching.tests)
        self.assertRaises(Exception, zcml) # ZCML conflict error
    
    def test_declareType(self):
        zcml = xmlconfig.XMLConfig("test3.zcml", z3c.caching.tests)
        zcml()
        
        rules = list(self.registry.enumerateTypes())
        rules.sort(lambda x,y: cmp(x.name, y.name))
        
        self.assertEquals(1, len(rules))
        self.assertEquals("rule1", rules[0].name)
        self.assertEquals(u"Rule 1", rules[0].title)
        self.assertEquals(u"Rule one", rules[0].description)
    
    def test_declareType_multiple(self):
        zcml = xmlconfig.XMLConfig("test4.zcml", z3c.caching.tests)
        self.assertRaises(Exception, zcml) # ZCML conflict error
    
    def test_declareType_explicit_after(self):
        i = TestView()
        self.failUnless(self.registry[i] is None)
        
        self.registry.explicit = True
        
        zcml = xmlconfig.XMLConfig("test5.zcml", z3c.caching.tests)
        zcml()
        
        rules = list(self.registry.enumerateTypes())
        rules.sort(lambda x,y: cmp(x.name, y.name))
        
        self.assertEquals(1, len(rules))
        self.assertEquals("rule1", rules[0].name)
        self.assertEquals(u"Rule 1", rules[0].title)
        self.assertEquals(u"Rule one", rules[0].description)
        
        i = TestView()
        self.assertEqual(self.registry[i], "rule1")

def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
