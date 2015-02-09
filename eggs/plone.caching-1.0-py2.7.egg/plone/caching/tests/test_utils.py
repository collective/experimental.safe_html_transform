import unittest

import zope.component.testing

from zope.interface import classProvides
from zope.component import provideUtility, getUtility

from plone.registry.interfaces import IRegistry
from plone.registry import Registry, Record, FieldRef
from plone.registry import field

from plone.caching.interfaces import ICachingOperationType
from plone.caching.utils import lookupOption, lookupOptions

_marker = object()

class TestLookupOption(unittest.TestCase):
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_lookupOption_no_registry(self):
        result = lookupOption('plone.caching.tests', 'testrule', 'test', default=_marker)
        self.failUnless(result is _marker)
        
    def test_lookupOption_no_record(self):
        provideUtility(Registry(), IRegistry)
        
        result = lookupOption('plone.caching.tests', 'testrule', 'test', default=_marker)
        self.failUnless(result is _marker)
    
    def test_lookupOption_default(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        
        registry.records['plone.caching.tests.test']  = Record(field.TextLine(), u"default")
        
        result = lookupOption('plone.caching.tests', 'testrule', 'test', default=_marker)
        self.assertEquals(u"default", result)
    
    def test_lookupOption_override(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        
        registry.records['plone.caching.tests.test'] = r = Record(field.TextLine(), u"default")
        registry.records['plone.caching.tests.testrule.test']  = Record(FieldRef(r.__name__, r.field), u"override")
        
        result = lookupOption('plone.caching.tests', 'testrule', 'test', default=_marker)
        self.assertEquals(u"override", result)

class TestLookupOptions(unittest.TestCase):
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_lookupOptions_no_registry(self):
        
        class DummyOperation(object):
            classProvides(ICachingOperationType)
            
            title = u""
            description = u""
            prefix = 'plone.caching.tests'
            options = ('test1', 'test2',)
        
        result = lookupOptions(DummyOperation, 'testrule', default=_marker)
        self.assertEquals({'test1': _marker, 'test2': _marker}, result)
        
    def test_lookupOptions_no_records(self):
        provideUtility(Registry(), IRegistry)
        
        class DummyOperation(object):
            classProvides(ICachingOperationType)
            
            title = u""
            description = u""
            prefix = 'plone.caching.tests'
            options = ('test1', 'test2',)
        
        result = lookupOptions(DummyOperation, 'testrule', default=_marker)
        self.assertEquals({'test1': _marker, 'test2': _marker}, result)
    
    def test_lookupOptions_default(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        
        registry.records['plone.caching.tests.test2'] = Record(field.TextLine(), u"foo")
        
        class DummyOperation(object):
            classProvides(ICachingOperationType)
            
            title = u""
            description = u""
            prefix = 'plone.caching.tests'
            options = ('test1', 'test2',)
        
        result = lookupOptions(DummyOperation, 'testrule', default=_marker)
        self.assertEquals({'test1': _marker, 'test2': u"foo"}, result)
    
    def test_lookupOptions_override(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        
        registry.records['plone.caching.tests.test1'] = Record(field.TextLine(), u"foo")
        registry.records['plone.caching.tests.test2'] = Record(field.TextLine(), u"bar")
        registry.records['plone.caching.tests.testrule.test2'] = Record(field.TextLine(), u"baz")
        
        class DummyOperation(object):
            classProvides(ICachingOperationType)
            
            title = u""
            description = u""
            prefix = 'plone.caching.tests'
            options = ('test1', 'test2',)
        
        result = lookupOptions(DummyOperation, 'testrule', default=_marker)
        self.assertEquals({'test1': u"foo", 'test2': u"baz"}, result)
    
    def test_lookupOptions_named(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        
        registry.records['plone.caching.tests.test2'] = Record(field.TextLine(), u"foo")
        
        class DummyOperation(object):
            classProvides(ICachingOperationType)
            
            title = u""
            description = u""
            prefix = 'plone.caching.tests'
            options = ('test1', 'test2',)
        
        provideUtility(DummyOperation, name=u"plone.caching.tests")
        
        result = lookupOptions(u"plone.caching.tests", 'testrule', default=_marker)
        self.assertEquals({'test1': _marker, 'test2': u"foo"}, result)
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
