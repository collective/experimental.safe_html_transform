import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

import time
from datetime import datetime
from dateutil.tz import tzlocal
from StringIO import StringIO

from zope.interface import implements
from zope.interface import Interface

from zope.component import getUtility
from zope.component import provideAdapter
from zope.component import provideUtility
from zope.component import adapts

from z3c.caching.interfaces import ILastModified

from plone.registry.interfaces import IRegistry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry import Registry

from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import Explicit
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPRequest import HTTPResponse
from Products.CMFCore.interfaces import IContentish

class DummyContext(Explicit):
    implements(IContentish)

class DummyPublished(object):

    def __init__(self, parent=None):
        self.__parent__ = parent

class TestETags(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(persistentFieldAdapter)

    # UserID

    def test_UserID_anonymous(self):
        from plone.app.caching.operations.etags import UserID

        class DummyPortalState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def member(self):
                return None

        provideAdapter(DummyPortalState, name=u"plone_portal_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = UserID(published, request)

        self.assertEqual(None, etag())

    def test_UserID_member(self):
        from plone.app.caching.operations.etags import UserID

        class DummyMember(object):

            def getId(self):
                return 'bob'

        class DummyPortalState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def member(self):
                return DummyMember()

        provideAdapter(DummyPortalState, name=u"plone_portal_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = UserID(published, request)

        self.assertEqual('bob', etag())


    # Roles

    def test_Roles_anonymous(self):
        from plone.app.caching.operations.etags import Roles

        class DummyPortalState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def anonymous(self):
                return True

            def member(self):
                return None

        provideAdapter(DummyPortalState, name=u"plone_portal_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = Roles(published, request)

        self.assertEqual('Anonymous', etag())

    def test_Roles_member(self):
        from plone.app.caching.operations.etags import Roles

        class DummyMember(object):

            def getRolesInContext(self, context):
                return ['Member', 'Manager']

        class DummyPortalState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def anonymous(self):
                return False

            def member(self):
                return DummyMember()

        provideAdapter(DummyPortalState, name=u"plone_portal_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = Roles(published, request)

        self.assertEqual('Manager;Member', etag())


    # Language

    def test_Language_no_header(self):
        from plone.app.caching.operations.etags import Language

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = Language(published, request)

        self.assertEqual('', etag())

    def test_Language_with_header(self):
        from plone.app.caching.operations.etags import Language

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        request.environ['HTTP_ACCEPT_LANGUAGE'] = 'en'

        etag = Language(published, request)

        self.assertEqual('en', etag())

    # UserLanguage

    def test_UserLanguage(self):
        from plone.app.caching.operations.etags import UserLanguage

        class DummyPortalState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def language(self):
                return 'en'

        provideAdapter(DummyPortalState, name=u"plone_portal_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = UserLanguage(published, request)

        self.assertEqual('en', etag())


    # GZip

    def test_GZip_no_registry(self):
        from plone.app.caching.operations.etags import GZip

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = GZip(published, request)

        self.assertEqual('0', etag())

    def test_GZip_disabled(self):
        from plone.app.caching.operations.etags import GZip

        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = False

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        request.environ['HTTP_ACCEPT_ENCODING'] = 'gzip; deflate'

        etag = GZip(published, request)

        self.assertEqual('0', etag())

    def test_GZip_not_accepted(self):
        from plone.app.caching.operations.etags import GZip

        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        request.environ['HTTP_ACCEPT_ENCODING'] = 'deflate'

        etag = GZip(published, request)

        self.assertEqual('0', etag())

    def test_GZip_enabled(self):
        from plone.app.caching.operations.etags import GZip

        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        request.environ['HTTP_ACCEPT_ENCODING'] = 'deflate; gzip'

        etag = GZip(published, request)

        self.assertEqual('1', etag())


    # LastModified

    def test_LastModified_no_adapter(self):
        from plone.app.caching.operations.etags import LastModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = LastModified(published, request)

        self.assertEqual(None, etag())

    def test_LastModified_None(self):
        from plone.app.caching.operations.etags import LastModified

        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return None

        provideAdapter(DummyLastModified)

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = LastModified(published, request)

        self.assertEqual(None, etag())

    def test_LastModified(self):
        from plone.app.caching.operations.etags import LastModified

        mod = datetime(2010, 1, 2, 3, 4, 5, 6, tzlocal())
        utcStamp = time.mktime(mod.utctimetuple())

        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return mod

        provideAdapter(DummyLastModified)

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = LastModified(published, request)
        self.assertEqual(str(utcStamp), etag())

    # CatalogCounter

    def test_CatalogCounter(self):
        from plone.app.caching.operations.etags import CatalogCounter

        class DummyCatalog(object):

            def getCounter(self):
                return 10

        class DummyTools(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def catalog(self):
                return DummyCatalog()

        provideAdapter(DummyTools, name=u"plone_tools")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = CatalogCounter(published, request)

        self.assertEqual('10', etag())


    # ObjectLocked

    def test_ObjectLocked_true(self):
        from plone.app.caching.operations.etags import ObjectLocked

        class DummyContextState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def is_locked(self):
                return True

        provideAdapter(DummyContextState, name=u"plone_context_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = ObjectLocked(published, request)

        self.assertEqual('1', etag())

    def test_ObjectLocked_false(self):
        from plone.app.caching.operations.etags import ObjectLocked

        class DummyContextState(object):
            implements(Interface)
            adapts(DummyContext, Interface)

            def __init__(self, context, request):
                pass

            def is_locked(self):
                return False

        provideAdapter(DummyContextState, name=u"plone_context_state")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        etag = ObjectLocked(published, request)

        self.assertEqual('0', etag())


    # Skin

    def test_Skin_request_variable(self):
        from plone.app.caching.operations.etags import Skin

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        class DummyPortalSkins(object):

            def getRequestVarname(self):
                return 'skin_name'

            def getDefaultSkin(self):
                return 'defaultskin'

        published.__parent__.portal_skins = DummyPortalSkins()
        request['skin_name'] = 'otherskin'

        etag = Skin(published, request)

        self.assertEqual('otherskin', etag())

    def test_Skin_default(self):
        from plone.app.caching.operations.etags import Skin

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished(DummyContext())

        class DummyPortalSkins(object):

            def getRequestVarname(self):
                return 'skin_name'

            def getDefaultSkin(self):
                return 'defaultskin'

        published.__parent__.portal_skins = DummyPortalSkins()

        etag = Skin(published, request)

        self.assertEqual('defaultskin', etag())
