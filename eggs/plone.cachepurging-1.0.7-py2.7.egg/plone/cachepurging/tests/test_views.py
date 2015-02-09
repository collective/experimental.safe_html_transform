import unittest
import zope.component.testing

from zope.interface import implements
from zope.component import adapts
from zope.component import adapter
from zope.component import provideUtility
from zope.component import provideAdapter
from zope.component import provideHandler

from z3c.caching.interfaces import IPurgePaths
from z3c.caching.interfaces import IPurgeEvent

from plone.registry.interfaces import IRegistry
from plone.registry import Registry

from plone.registry.fieldfactory import persistentFieldAdapter

from plone.cachepurging.interfaces import IPurger
from plone.cachepurging.interfaces import ICachePurgingSettings

from plone.cachepurging.browser import QueuePurge, PurgeImmediately

class FauxContext(object):
    pass

class FauxRequest(dict):
    pass

class Handler(object):

    def __init__(self):
        self.invocations = []

    @adapter(IPurgeEvent)
    def handler(self, event):
        self.invocations.append(event)

class TestQueuePurge(unittest.TestCase):

    def setUp(self):
        provideAdapter(persistentFieldAdapter)
        self.registry = Registry()
        self.registry.registerInterface(ICachePurgingSettings)
        provideUtility(self.registry, IRegistry)

        self.settings = self.registry.forInterface(ICachePurgingSettings)
        self.settings.enabled = True
        self.settings.cachingProxies = ('http://localhost:1234',)

        self.handler = Handler()
        provideHandler(self.handler.handler)

    def tearDown(self):
        zope.component.testing.tearDown()

    def test_disabled(self):
        self.settings.enabled = False

        view = QueuePurge(FauxContext(), FauxRequest())
        self.assertEqual('Caching not enabled', view())
        self.assertEqual([], self.handler.invocations)

    def test_enabled(self):
        self.settings.enabled = True

        context = FauxContext()
        view = QueuePurge(context, FauxRequest)
        self.assertEqual('Queued', view())
        self.assertEqual(1, len(self.handler.invocations))
        self.assertTrue(self.handler.invocations[0].object is context)

class TestPurgeImmediately(unittest.TestCase):

    def setUp(self):
        provideAdapter(persistentFieldAdapter)
        self.registry = Registry()
        self.registry.registerInterface(ICachePurgingSettings)
        provideUtility(self.registry, IRegistry)

        self.settings = self.registry.forInterface(ICachePurgingSettings)
        self.settings.enabled = True
        self.settings.cachingProxies = ('http://localhost:1234',)

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

        class FauxPurger(object):
            implements(IPurger)

            def purgeSync(self, url, httpVerb='PURGE'):
                return "200 OK", "cached", None

        provideUtility(FauxPurger())

    def tearDown(self):
        zope.component.testing.tearDown()

    def test_disabled(self):
        self.settings.enabled = False
        view = PurgeImmediately(FauxContext(), FauxRequest())
        self.assertEqual('Caching not enabled', view())

    def test_purge(self):
        view = PurgeImmediately(FauxContext(), FauxRequest())
        self.assertEqual("Purged http://localhost:1234/foo Status 200 OK X-Cache cached Error: None\n"
                          "Purged http://localhost:1234/bar Status 200 OK X-Cache cached Error: None\n",
                          view())

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
