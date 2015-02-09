from unittest import TestCase
import warnings
from zope.interface import Interface
from zope.interface import implements

from zope.component import provideAdapter
from zope.component import provideUtility

from z3c.caching.registry import RulesetRegistry
from z3c.caching.registry import getGlobalRulesetRegistry

import zope.component.testing

class ITestView(Interface):
    pass

class IMoreSpecificTestView(ITestView):
    pass

class TestView(object):
    implements(ITestView)

class OtherTestView(object):
    implements(IMoreSpecificTestView)

class IDummy(Interface):
    pass

class TestRulesetRegistry(TestCase):

    def setUp(self):
        provideAdapter(RulesetRegistry)
        self.registry = getGlobalRulesetRegistry()
    
    def tearDown(self):
        self.registry.clear()
        zope.component.testing.tearDown()

    def test_no_ruleset_returned_if_unregistered(self):
        self.failUnless(self.registry[None] is None)

    def test_ruleset_for_class(self):
        self.registry.register(TestView, "frop")
        i=TestView()
        self.assertEqual(self.registry[i], "frop")

    def test_ruleset_for_interface(self):
        self.registry.register(ITestView, "frop")
        i=TestView()
        self.assertEqual(self.registry[i], "frop")
    
    def test_most_specific_interface_wins(self):
        self.registry.register(ITestView, "frop")
        self.registry.register(IMoreSpecificTestView, "fribble")
        i=OtherTestView()
        self.assertEqual(self.registry[i], "fribble")
    
    def test_direct_lookup_for_interface_works(self):
        self.registry.register(ITestView, "frop")
        self.assertEqual(self.registry.directLookup(ITestView), "frop")

    def test_direct_lookup_for_daughter_fails(self):
        self.registry.register(ITestView, "frop")
        self.assertEqual(self.registry.directLookup(IMoreSpecificTestView), None)
    
    def test_registration_on_class_ignores_any_interface_relationship(self):
        self.registry.register(TestView, "frop")
        
        i=OtherTestView()
        self.assertEqual(self.registry[i], None)

        i=TestView()
        self.assertEqual(self.registry[i], "frop")

    def test_registration_on_class_wins_over_interface_registration(self):
        self.registry.register(ITestView, "frop")
        self.registry.register(TestView, "fribble")
        
        i=TestView()
        self.assertEqual(self.registry[i], "fribble")

    def test_ruleset_registered_twice(self):
        self.registry.register(ITestView, "frop")

        # Hide the warning generated, that's for users, not tests.
        warnings.simplefilter("ignore")
        self.registry.register(ITestView, "fribble")
        warnings.simplefilter("default")

        i=TestView()
        self.assertEqual(self.registry[i], "frop")

    def test_unregistering_ruleset_removes_ruleset(self):
        self.registry.register(TestView, "frop")
        self.registry.unregister(TestView)
        self.failUnless(self.registry[TestView] is None)

    def test_unregistering_nonexistant_ruleset_doesnt_error(self):
        self.failUnless(self.registry[TestView] is None)
        self.registry.unregister(TestView)
        self.failUnless(self.registry[TestView] is None)

    def test_clearing_registry_removes_rulesets(self):
        self.registry.register(ITestView, "frop")
        
        self.registry.clear()
        
        i = TestView()
        self.failUnless(self.registry[i] is None)

    def test_clearing_ignores_other_utilities(self):
        
        class DummyUtility(object):
            implements(IDummy)
        
        provideUtility(DummyUtility())
        
        self.registry.register(ITestView, "frop")
        
        self.registry.clear()
        
        i = TestView()
        self.failUnless(self.registry[i] is None)
    
    def test_clearing_registry_removes_types(self):
        self.registry.declareType("rule1", u"Rule 1", u"First rule")
        self.registry.declareType("rule2", u"Rule 2", u"Second rule")
        
        self.registry.register(ITestView, "frop")
        
        self.registry.clear()
        
        i = TestView()
        self.failUnless(self.registry[i] is None)
        self.assertEquals(0, len(list(self.registry.enumerateTypes())))
    
    def test_declareType_overrides(self):
        self.registry.declareType("rule1", u"Rule 1", u"First rule")
        self.registry.declareType("rule2", u"Rule 2", u"Second rule")
        self.registry.declareType("rule1", u"Rule One", u"Rule uno")
        
        rules = list(self.registry.enumerateTypes())
        rules.sort(lambda x,y: cmp(x.name, y.name))
        
        self.assertEquals(2, len(rules))
        self.assertEquals("rule1", rules[0].name)
        self.assertEquals(u"Rule One", rules[0].title)
        self.assertEquals(u"Rule uno", rules[0].description)
        self.assertEquals("rule2", rules[1].name)
        self.assertEquals(u"Rule 2", rules[1].title)
        self.assertEquals(u"Second rule", rules[1].description)
    
    def test_enumerateTypes(self):
        self.registry.declareType("rule1", u"Rule 1", u"First rule")
        self.registry.declareType("rule2", u"Rule 2", u"Second rule")
        
        rules = list(self.registry.enumerateTypes())
        rules.sort(lambda x,y: cmp(x.title, y.title))
        
        self.assertEquals(2, len(rules))
        self.assertEquals("rule1", rules[0].name)
        self.assertEquals(u"Rule 1", rules[0].title)
        self.assertEquals(u"First rule", rules[0].description)
        self.assertEquals("rule2", rules[1].name)
        self.assertEquals(u"Rule 2", rules[1].title)
        self.assertEquals(u"Second rule", rules[1].description)
    
    def test_enumerate_empty(self):
        self.assertEqual(set([]), set(self.registry.enumerateTypes()))
    
    def test_set_explicit_mode(self):
        self.registry.explicit = True
        
        self.assertRaises(LookupError, self.registry.register, TestView, "rule1")
        self.assertEquals(None, self.registry.lookup(TestView()))
        
        self.registry.declareType("rule1", u"Rule 1", u"First rule")
        self.registry.register(TestView, "rule1")
        
        self.assertEquals("rule1", self.registry.lookup(TestView()))
        
    def test_disable_explicit_mode(self):
        self.registry.explicit = True
        
        self.assertRaises(LookupError, self.registry.register, TestView, "rule1")
        self.assertEquals(None, self.registry.lookup(TestView()))
        
        self.registry.explicit = False
        
        self.registry.register(TestView, "rule1")
        self.assertEquals("rule1", self.registry.lookup(TestView()))

class TestConvenienceAPI(TestCase):

    def setUp(self):
        provideAdapter(RulesetRegistry)
        self.registry = getGlobalRulesetRegistry()
    
    def tearDown(self):
        self.registry.clear()
        zope.component.testing.tearDown()

    def test_no_ruleset_returned_if_unregistered(self):
        from z3c.caching.registry import lookup
        self.failUnless(lookup(None) is None)

    def test_ruleset_for_class(self):
        from z3c.caching.registry import register, lookup
        register(TestView, "frop")
        i=TestView()
        self.assertEqual(lookup(i), "frop")

    def test_ruleset_for_interface(self):
        from z3c.caching.registry import register, lookup
        register(ITestView, "frop")
        i=TestView()
        self.assertEqual(lookup(i), "frop")
    
    def test_most_specific_interface_wins(self):
        from z3c.caching.registry import register, lookup
        register(ITestView, "frop")
        register(IMoreSpecificTestView, "fribble")
        i=OtherTestView()
        self.assertEqual(lookup(i), "fribble")
    
    def test_unregistering_ruleset_removes_ruleset(self):
        from z3c.caching.registry import register, unregister, lookup
        register(TestView, "frop")
        unregister(TestView)
        self.failUnless(lookup(TestView) is None)

    def test_unregistering_nonexistant_ruleset_doesnt_error(self):
        from z3c.caching.registry import unregister, lookup
        self.failUnless(lookup(TestView) is None)
        unregister(TestView)
        self.failUnless(lookup(TestView) is None)
    
    def test_declareType_enumerateTypes(self):
        from z3c.caching.registry import declareType, enumerateTypes
        declareType("rule1", u"Rule 1", u"Rule one")
        
        rules = list(enumerateTypes())
        rules.sort(lambda x,y: cmp(x.name, y.name))
        
        self.assertEquals(1, len(rules))
        self.assertEquals("rule1", rules[0].name)
        self.assertEquals(u"Rule 1", rules[0].title)
        self.assertEquals(u"Rule one", rules[0].description)
    
    def test_set_explicit_mode(self):
        from z3c.caching.registry import setExplicitMode
        
        self.assertEquals(False, self.registry.explicit)
        setExplicitMode()
        self.assertEquals(True, self.registry.explicit)
        setExplicitMode(False)
        self.assertEquals(False, self.registry.explicit)
        setExplicitMode(True)
        self.assertEquals(True, self.registry.explicit)

class TestNotSetUp(TestCase):

    def test_getGlobalRulesetRegistry(self):
        from z3c.caching.registry import getGlobalRulesetRegistry
        self.assertEquals(None, getGlobalRulesetRegistry())
    
    def test_register(self):
        from z3c.caching.registry import register
        self.assertRaises(LookupError, register, TestView, 'testrule')
    
    def test_unregister(self):
        from z3c.caching.registry import unregister
        self.assertRaises(LookupError, unregister, TestView)
    
    def test_lookup(self):
        from z3c.caching.registry import lookup
        self.assertEquals(None, lookup(TestView))
    
    def test_enumerateTypes(self):
        from z3c.caching.registry import enumerateTypes
        self.assertRaises(LookupError, enumerateTypes)
    
    def test_declareType(self):
        from z3c.caching.registry import declareType
        self.assertRaises(LookupError, declareType, 'name', 'title', 'description')
    
    def test_setExplicitMode(self):
        from z3c.caching.registry import setExplicitMode
        self.assertRaises(LookupError, setExplicitMode)

def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

