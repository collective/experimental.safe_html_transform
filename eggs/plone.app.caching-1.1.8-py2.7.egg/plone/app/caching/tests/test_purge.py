import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

from zope.interface import implements

from zope.component import getUtility
from zope.component import adapter
from zope.component import adapts
from zope.component import provideHandler
from zope.component import provideUtility
from zope.component import provideAdapter

from zope.component.event import objectEventNotify

from zope.event import notify

from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectRemovedEvent
from zope.lifecycleevent import ObjectMovedEvent

from zope.globalrequest import setRequest

from plone.registry.interfaces import IRegistry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry import Registry

from z3c.caching.interfaces import IPurgeEvent
from z3c.caching.interfaces import IPurgePaths

from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import Explicit, aq_base
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IDiscussionResponse
from Products.Archetypes import atapi
from Products.Archetypes.Schema.factory import instanceSchemaFactory

from plone.app.caching.purge import purgeOnModified
from plone.app.caching.purge import purgeOnMovedOrRemoved

from plone.app.caching.purge import ContentPurgePaths
from plone.app.caching.purge import DiscussionItemPurgePaths
from plone.app.caching.purge import ObjectFieldPurgePaths

class Handler(object):

    def __init__(self):
        self.invocations = []

    @adapter(IPurgeEvent)
    def handler(self, event):
        self.invocations.append(event)

class FauxRequest(dict):
    pass

class FauxNonContent(Explicit):
    implements(IContentish)

    def __init__(self, name=None):
        self.__name__ = name
        self.__parent__ = None # may be overridden by acquisition

    def getId(self):
        return self.__name__

    def virtual_url_path(self):
        parent = aq_base(self.__parent__)
        if parent is not None:
            return parent.virtual_url_path() + '/' + self.__name__
        else:
            return self.__name__

    def getPhysicalPath(self):
        return ('', )

class FauxContent(FauxNonContent):
    implements(IBrowserDefault)

    portal_type = 'testtype'

    def defaultView(self):
        return 'default-view'

class FauxDiscussable(Explicit):
    implements(IDiscussionResponse)

class TestPurgeRedispatch(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        self.handler = Handler()
        provideHandler(self.handler.handler)

        provideHandler(objectEventNotify)
        provideHandler(purgeOnModified)
        provideHandler(purgeOnMovedOrRemoved)

        provideAdapter(persistentFieldAdapter)
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('testtype',)

    def test_not_purged(self):
        context = FauxNonContent('new').__of__(FauxContent())

        notify(ObjectModifiedEvent(context))
        notify(ObjectAddedEvent(context))
        notify(ObjectRemovedEvent(context))

        self.assertEqual(0, len(self.handler.invocations))

    def test_modified(self):
        context = FauxContent()

        notify(ObjectModifiedEvent(context))

        self.assertEqual(1, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

    def test_added(self):
        context = FauxContent('new').__of__(FauxContent())

        notify(ObjectAddedEvent(context, context.__parent__, 'new'))

        self.assertEqual(0, len(self.handler.invocations))

    def test_moved(self):
        context = FauxContent('new').__of__(FauxContent())

        notify(ObjectMovedEvent(context, FauxContent(), 'old',
                                context.__parent__, 'new'))

        self.assertEqual(1, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

    def test_renamed(self):
        context = FauxContent('new').__of__(FauxContent())

        notify(ObjectMovedEvent(context,
                                context.__parent__, 'old',
                                context.__parent__, 'new'))

        self.assertEqual(1, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

    def test_removed(self):
        context = FauxContent('new').__of__(FauxContent())

        notify(ObjectRemovedEvent(context, context.__parent__, 'new'))

        self.assertEqual(1, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

class TestContentPurgePaths(unittest.TestCase):

    layer = UNIT_TESTING

    def test_no_default_view(self):
        context = FauxNonContent('foo')
        purger = ContentPurgePaths(context)

        self.assertEqual(['/foo/', '/foo/view'],
                          list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_default_view(self):
        context = FauxContent('foo')
        purger = ContentPurgePaths(context)

        self.assertEqual(['/foo/', '/foo/view', '/foo/default-view'],
                          list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_parent_not_default_view(self):
        context = FauxContent('foo').__of__(FauxContent('bar'))
        purger = ContentPurgePaths(context)

        self.assertEqual(['/bar/foo/', '/bar/foo/view', '/bar/foo/default-view'],
                          list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_parent_default_view(self):
        context = FauxContent('default-view').__of__(FauxContent('bar'))
        purger = ContentPurgePaths(context)

        self.assertEqual(['/bar/default-view/', '/bar/default-view/view', '/bar/default-view/default-view',
                           '/bar', '/bar/', '/bar/view'],
                          list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

class TestDiscussionItemPurgePaths(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):

        class FauxContentPurgePaths(object):
            implements(IPurgePaths)
            adapts(FauxContent)

            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ['/' + self.context.virtual_url_path()]

            def getAbsolutePaths(self):
                return ['/purgeme']

        provideAdapter(FauxContentPurgePaths, name="testpurge")

    def test_no_tool(self):
        root = FauxContent('')
        content = FauxContent('foo').__of__(root)
        discussable = FauxDiscussable().__of__(content)

        request = FauxRequest()
        setRequest(request)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual([], list(purge.getRelativePaths()))
        self.assertEqual([], list(purge.getAbsolutePaths()))

    def test_no_request(self):
        root = FauxContent('app')
        content = FauxContent('foo').__of__(root)
        discussable = FauxDiscussable().__of__(content)

        class FauxPloneTool(object):

            def getDiscussionThread(self, item):
                return [content, item]

        root.plone_utils = FauxPloneTool()

        setRequest(None)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual([], list(purge.getRelativePaths()))
        self.assertEqual([], list(purge.getAbsolutePaths()))

    def test_no_discussion_thread(self):
        root = FauxContent('app')
        content = FauxContent('foo').__of__(root)
        discussable = FauxDiscussable().__of__(content)

        class FauxPloneTool(object):

            def getDiscussionThread(self, item):
                return []

        root.plone_utils = FauxPloneTool()

        request = FauxRequest()
        setRequest(request)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual([], list(purge.getRelativePaths()))
        self.assertEqual([], list(purge.getAbsolutePaths()))

    def test_paths_of_root(self):
        root = FauxContent('app')
        content = FauxContent('foo').__of__(root)
        discussable = FauxDiscussable().__of__(content)

        class FauxPloneTool(object):

            def getDiscussionThread(self, item):
                return [content, item]

        root.plone_utils = FauxPloneTool()

        request = FauxRequest()
        setRequest(request)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual(['/app/foo'], list(purge.getRelativePaths()))
        self.assertEqual(['/purgeme'], list(purge.getAbsolutePaths()))

class TestObjectFieldPurgePaths(unittest.TestCase):

    maxDiff = None
    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(instanceSchemaFactory)

    def test_no_file_image_fields(self):

        class ATNoFields(atapi.BaseContent):
            schema = atapi.Schema((atapi.StringField('foo'),))

        context = ATNoFields('foo')
        purger = ObjectFieldPurgePaths(context)

        self.assertEqual([], list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_file_image_fields(self):
        from plone.app.blob.field import BlobField

        class ATMultipleFields(atapi.BaseContent):
            schema = atapi.Schema((
                    atapi.StringField('foo'),
                    atapi.FileField('file1'),
                    atapi.ImageField('image1'),
                    atapi.ImageField('image2', sizes={'mini': (50,50), 'normal' : (100,100)}),
                    BlobField('blob1'),
                ))

        root = FauxContent('')
        context = ATMultipleFields('foo').__of__(root)
        purger = ObjectFieldPurgePaths(context)

        self.assertEqual(['/foo/download', '/foo/at_download',
                           '/foo/at_download/file1', '/foo/file1',
                           '/foo/at_download/image1', '/foo/image1','/foo/image1_thumb',
                           '/foo/at_download/image2', '/foo/image2', '/foo/image2_mini', '/foo/image2_normal',
                           '/foo/at_download/blob1', '/foo/blob1'],
                           list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_file_image_text_fields(self):

        class ATMultipleFields(atapi.BaseContent):
            schema = atapi.Schema((
                    atapi.StringField('foo'),
                    atapi.FileField('file1'),
                    atapi.ImageField('image1'),
                    atapi.ImageField('image2', sizes={'mini': (50,50), 'normal' : (100,100)}),
                    atapi.TextField('text'),
                ))

        root = FauxContent('')
        context = ATMultipleFields('foo').__of__(root)
        purger = ObjectFieldPurgePaths(context)

        self.assertEqual(['/foo/download', '/foo/at_download',
                           '/foo/at_download/file1', '/foo/file1',
                           '/foo/at_download/image1', '/foo/image1','/foo/image1_thumb',
                           '/foo/at_download/image2', '/foo/image2', '/foo/image2_mini', '/foo/image2_normal'],
                           list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))
