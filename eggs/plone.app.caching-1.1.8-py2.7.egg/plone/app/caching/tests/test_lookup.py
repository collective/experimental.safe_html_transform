import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

from z3c.caching.registry import RulesetRegistry
import z3c.caching.registry

from zope.component import provideUtility, provideAdapter, getUtility
from zope.interface import implements

from plone.registry.interfaces import IRegistry

from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter

from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.lookup import ContentItemLookup

from Acquisition import Explicit
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from Products.Five.browser import BrowserView

class DummyContent(Explicit):
    implements(IBrowserDefault, IDynamicType)

    def __init__(self, portal_type='testtype', defaultView='defaultView'):
        self.portal_type = portal_type
        self._defaultView = defaultView

    def defaultView(self):
        return self._defaultView

class DummyNotContent(Explicit):
    pass

class DummyFTI(object):

    def __init__(self, portal_type, viewAction=''):
        self.id = portal_type
        self._actions = {
                'object/view': {'url': viewAction},
            }

    def getActionInfo(self, name):
        return self._actions[name]

    def queryMethodID(self, id, default=None, context=None):
        if id == '(Default)':
            return 'defaultView'
        elif id == 'view':
            return '@@defaultView'
        return default

class DummyNotBrowserDefault(Explicit):
    implements(IDynamicType)

    def __init__(self, portal_type='testtype', viewAction=''):
        self.portal_type = portal_type
        self._viewAction = viewAction

    def getTypeInfo(self):
        return DummyFTI(self.portal_type, self._viewAction)

class DummyResponse(dict):

    def addHeader(self, name, value):
        self.setdefault(name, []).append(value)

class DummyRequest(dict):
    def __init__(self, published, response):
        self['PUBLISHED'] = published
        self.response = response

class DummyView(BrowserView):
    __name__ = 'defaultView'

class TestContentItemLookup(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(persistentFieldAdapter)
        provideAdapter(RulesetRegistry)

    def test_no_registry(self):
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())

        self.assertEqual(None, ContentItemLookup(published, request)())

    def test_no_mappings(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        self.assertEqual(None, ContentItemLookup(published, request)())

    def test_template_lookup(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'someView': 'rule1'}

        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_contenttype_name_lookup(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}

        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_contenttype_class_lookup_page_template(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {}

        z3c.caching.registry.register(DummyContent, 'rule1')

        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_contenttype_class_lookup_browser_view(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {}

        z3c.caching.registry.register(DummyContent, 'rule1')

        published = DummyView(DummyContent(), None)
        request = DummyRequest(published, DummyResponse())
        published.request = published

        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_contenttype_class_lookup_template_override(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'defaultView': 'rule2'}
        ploneSettings.contentTypeRulesetMapping = {}

        z3c.caching.registry.register(DummyContent, 'rule1')

        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule2', ContentItemLookup(published, request)())

    def test_contenttype_class_lookup_type_override(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule2'}

        z3c.caching.registry.register(DummyContent, 'rule1')

        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule2', ContentItemLookup(published, request)())

    def test_contenttype_not_default_view(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}

        published = ZopePageTemplate('someView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEqual(None, ContentItemLookup(published, request)())

    def test_parent_not_content(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}

        published = ZopePageTemplate('defaultView').__of__(DummyNotContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEqual(None, ContentItemLookup(published, request)())

    def test_parent_not_IBrowserDefault_methodid(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}

        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/view'))
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_parent_not_IBrowserDefault_default_method(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}

        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/'))
        request = DummyRequest(published, DummyResponse())
        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_parent_not_IBrowserDefault_actiononly(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}

        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/defaultView'))
        request = DummyRequest(published, DummyResponse())

        self.assertEqual('rule1', ContentItemLookup(published, request)())

    def test_match_template_and_content(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'defaultView': 'rule1'}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule2'}

        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())

        self.assertEqual('rule1', ContentItemLookup(published, request)())
