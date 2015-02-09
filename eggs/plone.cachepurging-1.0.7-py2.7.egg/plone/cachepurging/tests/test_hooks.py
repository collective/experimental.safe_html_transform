import unittest
import zope.component.testing

from zope.interface import implements
from zope.interface import alsoProvides

from zope.component import adapts
from zope.component import provideUtility
from zope.component import provideAdapter
from zope.component import provideHandler

from zope.event import notify

from zope.annotation.attribute import AttributeAnnotations
from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable

from zope.globalrequest import setRequest

from z3c.caching.interfaces import IPurgePaths
from z3c.caching.purge import Purge

from plone.registry.interfaces import IRegistry
from plone.registry import Registry

from plone.registry.fieldfactory import persistentFieldAdapter

from plone.cachepurging.interfaces import IPurger
from plone.cachepurging.interfaces import ICachePurgingSettings

from plone.cachepurging.hooks import queuePurge, purge

from ZPublisher.pubevents import PubSuccess

class FauxContext(dict):
    pass

class FauxRequest(dict):
    pass

class TestQueueHandler(unittest.TestCase):

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        provideAdapter(persistentFieldAdapter)
        provideHandler(queuePurge)

    def tearDown(self):
        zope.component.testing.tearDown()
        setRequest(None)

    def test_no_request(self):
        context = FauxContext()

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return []

        provideAdapter(FauxPurgePaths, name="test1")

        try:
            notify(Purge(context))
        except:
            self.fail()

    def test_request_not_annotatable(self):
        context = FauxContext()

        request = FauxRequest()
        setRequest(request)

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return []

        provideAdapter(FauxPurgePaths, name="test1")

        try:
            notify(Purge(context))
        except:
            self.fail()


    def test_no_registry(self):
        context = FauxContext()

        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)
        setRequest(request)

        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return []

        provideAdapter(FauxPurgePaths, name="test1")

        notify(Purge(context))

        self.assertEqual({}, dict(IAnnotations(request)))

    def test_caching_disabled(self):
        context = FauxContext()

        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)
        setRequest(request)

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = False
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return []

        provideAdapter(FauxPurgePaths, name="test1")

        notify(Purge(context))

        self.assertEqual({}, dict(IAnnotations(request)))

    def test_enabled_no_paths(self):
        context = FauxContext()

        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)
        setRequest(request)

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        notify(Purge(context))

        self.assertEqual({'plone.cachepurging.urls': set()},
                          dict(IAnnotations(request)))

    def test_enabled(self):
        context = FauxContext()

        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)
        setRequest(request)

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContext)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/foo', '/bar']

            def getAbsolutePaths(self):
                return []

        provideAdapter(FauxPurgePaths, name="test1")

        notify(Purge(context))

        self.assertEqual({'plone.cachepurging.urls': set(['/foo', '/bar'])},
                          dict(IAnnotations(request)))

class TestPurgeHandler(unittest.TestCase):

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        provideAdapter(persistentFieldAdapter)
        provideHandler(purge)

    def tearDown(self):
        zope.component.testing.tearDown()

    def test_request_not_annotatable(self):
        request = FauxRequest()

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurger(object):
            implements(IPurger)

            def __init__(self):
                self.purged = []

            def purgeAsync(self, url, httpVerb='PURGE'):
                self.purged.append(url)

        purger = FauxPurger()
        provideUtility(purger)

        notify(PubSuccess(request))

        self.assertEqual([], purger.purged)

    def test_no_path_key(self):
        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurger(object):
            implements(IPurger)

            def __init__(self):
                self.purged = []

            def purgeAsync(self, url, httpVerb='PURGE'):
                self.purged.append(url)

        purger = FauxPurger()
        provideUtility(purger)

        notify(PubSuccess(request))

        self.assertEqual([], purger.purged)

    def test_no_paths(self):
        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)

        IAnnotations(request)['plone.cachepurging.urls'] = set()

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurger(object):
            implements(IPurger)

            def __init__(self):
                self.purged = []

            def purgeAsync(self, url, httpVerb='PURGE'):
                self.purged.append(url)

        purger = FauxPurger()
        provideUtility(purger)

        notify(PubSuccess(request))

        self.assertEqual([], purger.purged)

    def test_no_registry(self):
        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)

        IAnnotations(request)['plone.cachepurging.urls'] = set(['/foo', '/bar'])

        class FauxPurger(object):
            implements(IPurger)

            def __init__(self):
                self.purged = []

            def purgeAsync(self, url, httpVerb='PURGE'):
                self.purged.append(url)

        purger = FauxPurger()
        provideUtility(purger)

        notify(PubSuccess(request))

        self.assertEqual([], purger.purged)

    def test_caching_disabled(self):
        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)

        IAnnotations(request)['plone.cachepurging.urls'] = set(['/foo', '/bar'])

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = False
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurger(object):
            implements(IPurger)

            def __init__(self):
                self.purged = []

            def purgeAsync(self, url, httpVerb='PURGE'):
                self.purged.append(url)

        purger = FauxPurger()
        provideUtility(purger)

        notify(PubSuccess(request))

        self.assertEqual([], purger.purged)

    def test_no_purger(self):
        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)

        IAnnotations(request)['plone.cachepurging.urls'] = set(['/foo', '/bar'])

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        try:
            notify(PubSuccess(request))
        except:
            self.fail()

    def test_purge(self):
        request = FauxRequest()
        alsoProvides(request, IAttributeAnnotatable)

        IAnnotations(request)['plone.cachepurging.urls'] = set(['/foo', '/bar'])

        registry = Registry()
        registry.registerInterface(ICachePurgingSettings)
        provideUtility(registry, IRegistry)

        settings = registry.forInterface(ICachePurgingSettings)
        settings.enabled = True
        settings.cachingProxies = ('http://localhost:1234',)

        class FauxPurger(object):
            implements(IPurger)

            def __init__(self):
                self.purged = []

            def purgeAsync(self, url, httpVerb='PURGE'):
                self.purged.append(url)

        purger = FauxPurger()
        provideUtility(purger)

        notify(PubSuccess(request))

        self.assertEqual(['http://localhost:1234/foo', 'http://localhost:1234/bar'],
                          purger.purged)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

