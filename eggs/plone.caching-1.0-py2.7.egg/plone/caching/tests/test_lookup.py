import unittest

import zope.component.testing

from zope.component import provideAdapter

from z3c.caching.registry import RulesetRegistry
import z3c.caching.registry

from plone.caching.lookup import DefaultRulesetLookup

class DummyView(object):
    pass

class DummyResponse(dict):
    
    def addHeader(self, name, value):
        self.setdefault(name, []).append(value)

class DummyRequest(dict):
    def __init__(self, published, response):
        self['PUBLISHED'] = published
        self.response = response

class TestLookup(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(RulesetRegistry)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_no_cache_rule(self):
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        self.assertEquals(None, DefaultRulesetLookup(view, request)())
        
    def test_match(self):
        z3c.caching.registry.register(DummyView, 'testrule')
        view = DummyView()
        request = DummyRequest(view, DummyResponse())        
        self.assertEquals('testrule', DefaultRulesetLookup(view, request)())

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)