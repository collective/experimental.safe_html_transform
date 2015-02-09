import unittest

import zope.component.testing

from zope.interface import implements
from zope.interface import Interface
from z3c.caching.registry import RulesetRegistry

from zope.component import provideUtility
from zope.component import provideAdapter
from zope.component import adapts

from plone.registry.interfaces import IRegistry
from plone.registry import Registry, Record
from plone.registry import field

from plone.caching.operations import Chain
from plone.caching.interfaces import ICachingOperation

_marker = object()

class DummyView(object):
    pass

class DummyResponse(dict):
    
    def addHeader(self, name, value):
        self.setdefault(name, []).append(value)
    
    def setHeader(self, name, value):
        self[name] = value

class DummyRequest(dict):
    def __init__(self, published, response):
        self['PUBLISHED'] = published
        self.response = response


class TestChain(unittest.TestCase):
    
    def setUp(self):
        self.registry = Registry()
        provideUtility(self.registry, IRegistry)
        provideAdapter(RulesetRegistry)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_no_option(self):
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        
        chain = Chain(view, request)
        ret = chain.interceptResponse('testrule', request.response)
        chain.modifyResponse('testrule', request.response)
        
        self.assertEquals(None, ret)
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({}, dict(request.response))
    
    def test_operations_list_not_set(self):
        
        self.registry.records["%s.operations" % Chain.prefix] = Record(field.List())
        
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        
        chain = Chain(view, request)
        ret = chain.interceptResponse('testrule', request.response)
        chain.modifyResponse('testrule', request.response)
        
        self.assertEquals(None, ret)
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({}, dict(request.response))
    
    def test_operations_empty(self):
        
        self.registry.records["%s.operations" % Chain.prefix] = Record(field.List(), [])
        
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        
        chain = Chain(view, request)
        ret = chain.interceptResponse('testrule', request.response)
        chain.modifyResponse('testrule', request.response)
        
        self.assertEquals(None, ret)
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({}, dict(request.response))
    
    def test_chained_operations_not_found(self):
        
        self.registry.records["%s.operations" % Chain.prefix] = Record(field.List(), ['op1'])
        
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        
        chain = Chain(view, request)
        chain.modifyResponse('testrule', request.response)
        
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({}, dict(request.response))
    
    def test_multiple_operations_one_found(self):
        self.registry.records["%s.operations" % Chain.prefix] = Record(field.List(), ['op1', 'op2'])
        
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        
        class DummyOperation(object):
            implements(ICachingOperation)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def interceptResponse(self, rulename, response):
                return u"foo"
            
            def modifyResponse(self, rulename, response):
                response['X-Mutated'] = rulename
        
        provideAdapter(DummyOperation, name="op2")
        
        chain = Chain(view, request)
        ret = chain.interceptResponse('testrule', request.response)
        
        self.assertEquals(u"foo", ret)
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({'X-Cache-Chain-Operations': 'op2'}, dict(request.response))
        
        request = DummyRequest(view, DummyResponse())
        chain = Chain(view, request)
        chain.modifyResponse('testrule', request.response)
        
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({'X-Mutated': 'testrule',
                           'X-Cache-Chain-Operations': 'op2'}, dict(request.response))

    def test_multiple_operations_multiple_found(self):
        self.registry.records["%s.operations" % Chain.prefix] = Record(field.List(), ['op1', 'op2'])
        
        view = DummyView()
        request = DummyRequest(view, DummyResponse())
        
        class DummyOperation1(object):
            implements(ICachingOperation)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def interceptResponse(self, rulename, response):
                return u"foo"
            
            def modifyResponse(self, rulename, response):
                response['X-Mutated-1'] = rulename
        
        provideAdapter(DummyOperation1, name="op1")
        
        class DummyOperation2(object):
            implements(ICachingOperation)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def interceptResponse(self, rulename, response):
                return u"bar"
            
            def modifyResponse(self, rulename, response):
                response['X-Mutated-2'] = rulename
        
        provideAdapter(DummyOperation2, name="op2")
        
        chain = Chain(view, request)
        ret = chain.interceptResponse('testrule', request.response)
        
        self.assertEquals(u"foo", ret)
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({'X-Cache-Chain-Operations': 'op1'}, dict(request.response))
        
        request = DummyRequest(view, DummyResponse())
        chain = Chain(view, request)
        chain.modifyResponse('testrule', request.response)
        
        self.assertEquals({'PUBLISHED': view}, dict(request))
        self.assertEquals({'X-Mutated-1': 'testrule',
                           'X-Mutated-2': 'testrule',
                           'X-Cache-Chain-Operations': 'op1; op2'}, dict(request.response))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
