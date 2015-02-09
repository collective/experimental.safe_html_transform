import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

from zope.interface import implements
from zope.component import provideUtility, provideAdapter, getUtility

from plone.registry.interfaces import IRegistry

from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter

from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import Explicit
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault

from plone.app.caching.utils import isPurged
from plone.app.caching.utils import getObjectDefaultView


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

class TestIsPurged(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(persistentFieldAdapter)

    def test_no_registry(self):
        content = DummyContent()
        self.assertEqual(False, isPurged(content))

    def test_no_settings(self):
        provideUtility(Registry(), IRegistry)
        content = DummyContent()
        self.assertEqual(False, isPurged(content))

    def test_no_portal_type(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('testtype',)

        content = DummyNotContent()
        self.assertEqual(False, isPurged(content))

    def test_not_listed(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('File', 'Image',)

        content = DummyContent()
        self.assertEqual(False, isPurged(content))

    def test_listed(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('File', 'Image', 'testtype',)

        content = DummyContent()
        self.assertEqual(True, isPurged(content))

class TestGetObjectDefaultPath(unittest.TestCase):

    layer = UNIT_TESTING

    def test_not_content(self):
        context = DummyNotContent()
        self.assertEqual(None, getObjectDefaultView(context))

    def test_browserdefault(self):
        context = DummyContent()
        self.assertEqual('defaultView', getObjectDefaultView(context))

    def test_not_IBrowserDefault_methodid(self):
        context = DummyNotBrowserDefault('testtype', 'string:${object_url}/view')
        self.assertEqual('defaultView', getObjectDefaultView(context))

    def test_not_IBrowserDefault_default_method(self):
        context = DummyNotBrowserDefault('testtype', 'string:${object_url}/')
        self.assertEqual('defaultView', getObjectDefaultView(context))

    def test_not_IBrowserDefault_actiononly(self):
        context = DummyNotBrowserDefault('testtype', 'string:${object_url}/defaultView')
        self.assertEqual('defaultView', getObjectDefaultView(context))
