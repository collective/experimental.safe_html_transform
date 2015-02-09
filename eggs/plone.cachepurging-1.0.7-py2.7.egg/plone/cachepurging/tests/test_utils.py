import unittest
import zope.component.testing

from zope.interface import implements
from zope.component import provideUtility
from zope.component import provideAdapter
from zope.component import adapts

from z3c.caching.interfaces import IPurgePaths

from plone.registry.interfaces import IRegistry
from plone.registry import Registry

from plone.registry.fieldfactory import persistentFieldAdapter

from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurgePathRewriter

from plone.cachepurging import utils

class FauxContext(object):
    pass

class FauxRequest(dict):
    pass

class TestIsCachingEnabled(unittest.TestCase):

    def setUp(self):
        provideAdapter(persistentFieldAdapter)

    def tearDown(self):
        zope.component.testing.tearDown()

    def test_no_registry(self):
        self.assertEqual(False, utils.isCachePurgingEnabled())

    def test_no_settings(self):
        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)
        self.assertEqual(False, utils.isCachePurgingEnabled())

    def test_disabled(self):
        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = False
        settings.cachingProxies = ('http://localhost:1234',)

        self.assertEqual(False, utils.isCachePurgingEnabled())

    def test_no_proxies(self):
        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = False

        settings.cachingProxies = None
        self.assertEqual(False, utils.isCachePurgingEnabled())

        settings.cachingProxies = ()
        self.assertEqual(False, utils.isCachePurgingEnabled())

    def test_enabled(self):
        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)
        self.assertEqual(True, utils.isCachePurgingEnabled())

    def test_passed_registry(self):
        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        self.assertEqual(False, utils.isCachePurgingEnabled())
        self.assertEqual(True, utils.isCachePurgingEnabled(registry))

class TestGetPathsToPurge(unittest.TestCase):

    def setUp(self):
        self.context = FauxContext()
        self.request = FauxRequest()

    def tearDown(self):
        zope.component.testing.tearDown()

    def test_no_purge_paths(self):
        self.assertEqual([], list(utils.getPathsToPurge(self.context, self.request)))

    def test_empty_relative_paths(self):

        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return []

            def getAbsolutePaths(self):
                return []

        provideAdapter(FauxPurgePaths, name="test1")

        self.assertEqual([], list(utils.getPathsToPurge(self.context, self.request)))

    def test_no_rewriter(self):
        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return ['/baz']

        provideAdapter(FauxPurgePaths, name="test1")

        self.assertEqual(['/foo', '/bar', '/baz'],
            list(utils.getPathsToPurge(self.context, self.request)))

    def test_test_rewriter(self):
        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return ['/baz']

        provideAdapter(FauxPurgePaths, name="test1")

        class DefaultRewriter(object):
            implements(IPurgePathRewriter)
            adapts(FauxRequest)

            def __init__(self, request):
                self.request = request

            def __call__(self, path):
                return ['/vhm1' + path, '/vhm2' + path]

        provideAdapter(DefaultRewriter)

        self.assertEqual(['/vhm1/foo', '/vhm2/foo',
                           '/vhm1/bar', '/vhm2/bar',
                           '/baz'],
            list(utils.getPathsToPurge(self.context, self.request)))

    def test_multiple_purge_paths(self):
        class FauxPurgePaths1(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return ['/baz']

        provideAdapter(FauxPurgePaths1, name="test1")

        class FauxPurgePaths2(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo/view']

            def getAbsolutePaths(self):
                return ['/quux']

        provideAdapter(FauxPurgePaths2, name="test2")

        class DefaultRewriter(object):
            implements(IPurgePathRewriter)
            adapts(FauxRequest)

            def __init__(self, request):
                self.request = request

            def __call__(self, path):
                return ['/vhm1' + path, '/vhm2' + path]

        provideAdapter(DefaultRewriter)

        self.assertEqual(['/vhm1/foo', '/vhm2/foo', '/vhm1/bar', '/vhm2/bar', '/baz',
                           '/vhm1/foo/view', '/vhm2/foo/view', '/quux'],
            list(utils.getPathsToPurge(self.context, self.request)))

    def test_rewriter_abort(self):
        class FauxPurgePaths1(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return ['/baz']

        provideAdapter(FauxPurgePaths1, name="test1")

        class FauxPurgePaths2(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo/view']

            def getAbsolutePaths(self):
                return ['/quux']

        provideAdapter(FauxPurgePaths2, name="test2")

        class DefaultRewriter(object):
            implements(IPurgePathRewriter)
            adapts(FauxRequest)

            def __init__(self, request):
                self.request = request

            def __call__(self, path):
                return []

        provideAdapter(DefaultRewriter)

        self.assertEqual(['/baz', '/quux'],
            list(utils.getPathsToPurge(self.context, self.request)))

class TestGetURLsToPurge(unittest.TestCase):

    def test_no_proxies(self):
        self.assertEqual([], list(utils.getURLsToPurge('/foo', [])))

    def test_absolute_path(self):
        self.assertEqual(['http://localhost:1234/foo/bar', 'http://localhost:2345/foo/bar'],
            list(utils.getURLsToPurge('/foo/bar', ['http://localhost:1234', 'http://localhost:2345/'])))

    def test_relative_path(self):
        self.assertEqual(['http://localhost:1234/foo/bar', 'http://localhost:2345/foo/bar'],
            list(utils.getURLsToPurge('foo/bar', ['http://localhost:1234', 'http://localhost:2345/'])))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
