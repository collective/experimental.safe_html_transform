import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

import time
import datetime
import dateutil.parser
import dateutil.tz
import wsgiref.handlers
from StringIO import StringIO

from zope.interface import implements
from zope.interface import Interface
from zope.interface import classImplements
from zope.interface import alsoProvides

from zope.component import provideAdapter
from zope.component import provideUtility
from zope.component import adapts

from plone.memoize.interfaces import ICacheChooser

from z3c.caching.interfaces import ILastModified

from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPRequest import HTTPResponse

from OFS.SimpleItem import SimpleItem

from Products.CMFCore.interfaces import IContentish

class DummyPublished(object):

    def __init__(self, parent=None):
        self.__parent__ = parent

def normalize_response_cache(value):
    # Zope < 2.13 incorrectly includes the HTTP status as a header;
    # Zope 2.13 does not
    if isinstance(value, tuple) and 'status' in value[1]:
        del value[1]['status']
    return value


class ResponseModificationHelpersTest(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)

    # doNotCache()

    def test_doNotCache(self):
        from plone.app.caching.operations.utils import doNotCache

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())

        doNotCache(published, request, response)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEqual(None, response.getHeader('Last-Modified'))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)

    def test_doNotCache_deletes_last_modified(self):
        from plone.app.caching.operations.utils import doNotCache

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        response.setHeader('Last-Modified', wsgiref.handlers.format_date_time(time.mktime(now.timetuple())))

        doNotCache(published, request, response)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEqual(None, response.getHeader('Last-Modified'))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)


    # cacheInBrowser()

    def test_cacheInBrowser_no_etag_no_last_modified(self):
        from plone.app.caching.operations.utils import cacheInBrowser

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())

        cacheInBrowser(published, request, response)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEqual(None, response.getHeader('Last-Modified'))
        self.assertEqual(None, response.getHeader('ETag', literal=1))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)

    def test_cacheInBrowser_etag(self):
        from plone.app.caching.operations.utils import cacheInBrowser

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"

        cacheInBrowser(published, request, response, etag=etag)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEqual(None, response.getHeader('Last-Modified'))
        self.assertEqual('"|foo|bar|"', response.getHeader('ETag', literal=1))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)

    def test_cacheInBrowser_lastModified(self):
        from plone.app.caching.operations.utils import cacheInBrowser

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))

        cacheInBrowser(published, request, response, lastModified=now)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEqual(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEqual(None, response.getHeader('ETag', literal=1))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)

    def test_cacheInBrowser_lastModified_and_etag(self):
        from plone.app.caching.operations.utils import cacheInBrowser

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"

        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))

        cacheInBrowser(published, request, response, etag=etag, lastModified=now)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEqual(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEqual('"|foo|bar|"', response.getHeader('ETag', literal=1))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)


    # cacheInProxy()

    def test_cacheInProxy_minimal(self):
        from plone.app.caching.operations.utils import cacheInProxy

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())

        cacheInProxy(published, request, response, smaxage=60)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, s-maxage=60, must-revalidate', response.getHeader('Cache-Control'))
        self.assertEqual(None, response.getHeader('Last-Modified'))
        self.assertEqual(None, response.getHeader('ETag', literal=1))
        self.assertEqual(None, response.getHeader('Vary'))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)

    def test_cacheInProxy_full(self):
        from plone.app.caching.operations.utils import cacheInProxy

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = '|foo|bar|'
        vary = 'Accept-Language'

        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))

        cacheInProxy(published, request, response, smaxage=60, etag=etag, lastModified=now, vary=vary)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=0, s-maxage=60, must-revalidate', response.getHeader('Cache-Control'))
        self.assertEqual(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEqual('"|foo|bar|"', response.getHeader('ETag', literal=1))
        self.assertEqual('Accept-Language', response.getHeader('Vary'))

        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.assertTrue(now > expires)


    # cacheInBrowserAndProxy()

    def test_cacheInBrowserAndProxy_minimal(self):
        from plone.app.caching.operations.utils import cacheInBrowserAndProxy

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())

        cacheInBrowserAndProxy(published, request, response, maxage=60)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=60, proxy-revalidate, public', response.getHeader('Cache-Control'))
        self.assertEqual(None, response.getHeader('Last-Modified'))
        self.assertEqual(None, response.getHeader('ETag', literal=1))
        self.assertEqual(None, response.getHeader('Vary'))

        timedelta = dateutil.parser.parse(response.getHeader('Expires')) - now
        self.assertFalse(timedelta < datetime.timedelta(seconds=59))
        self.assertFalse(timedelta > datetime.timedelta(seconds=60))

    def test_cacheInBrowserAndProxy_full(self):
        from plone.app.caching.operations.utils import cacheInBrowserAndProxy

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = '|foo|bar|'
        vary = 'Accept-Language'

        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))

        cacheInBrowserAndProxy(published, request, response, maxage=60, etag=etag, lastModified=now, vary=vary)

        self.assertEqual(200, response.getStatus())
        self.assertEqual('max-age=60, proxy-revalidate, public', response.getHeader('Cache-Control'))
        self.assertEqual(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEqual('"|foo|bar|"', response.getHeader('ETag', literal=1))
        self.assertEqual('Accept-Language', response.getHeader('Vary'))

        timedelta = dateutil.parser.parse(response.getHeader('Expires')) - now
        self.assertFalse(
            timedelta < datetime.timedelta(seconds=58),
            "%s is not < %s" % (timedelta, datetime.timedelta(seconds=58))
        )
        self.assertFalse(
            timedelta > datetime.timedelta(seconds=61),
            "%s is not > %s" % (timedelta, datetime.timedelta(seconds=61))
        )


    # cacheInRAM()

    def test_cacheInRAM_no_etag(self):
        from plone.app.caching.operations.utils import cacheInRAM
        from plone.app.caching.operations.utils import PAGE_CACHE_ANNOTATION_KEY

        from plone.app.caching.interfaces import IRAMCached

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        request.environ['PATH_INFO'] = '/foo'

        assert not IRAMCached.providedBy(response)

        cacheInRAM(published, request, response)

        annotations = IAnnotations(request)
        self.assertEqual("http://example.com/foo?", annotations[PAGE_CACHE_ANNOTATION_KEY])
        self.assertTrue(IRAMCached.providedBy(request))

    def test_cacheInRAM_etag(self):
        from plone.app.caching.operations.utils import cacheInRAM
        from plone.app.caching.operations.utils import PAGE_CACHE_ANNOTATION_KEY

        from plone.app.caching.interfaces import IRAMCached

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        request.environ['PATH_INFO'] = '/foo'
        etag = '|foo|bar|'

        assert not IRAMCached.providedBy(response)

        cacheInRAM(published, request, response, etag=etag)

        annotations = IAnnotations(request)
        self.assertEqual("||foo|bar|||http://example.com/foo?", annotations[PAGE_CACHE_ANNOTATION_KEY])
        self.assertTrue(IRAMCached.providedBy(request))

    def test_cacheInRAM_etag_alternate_key(self):
        from plone.app.caching.operations.utils import cacheInRAM

        from plone.app.caching.interfaces import IRAMCached

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        request.environ['PATH_INFO'] = '/foo'
        etag = '|foo|bar|'

        assert not IRAMCached.providedBy(response)

        cacheInRAM(published, request, response, etag=etag, annotationsKey="alt.key")

        annotations = IAnnotations(request)
        self.assertEqual("||foo|bar|||http://example.com/foo?", annotations["alt.key"])
        self.assertTrue(IRAMCached.providedBy(request))


class ResponseInterceptorHelpersTest(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)

    # cachedResponse()

    def test_cachedResponse(self):
        from plone.app.caching.operations.utils import cachedResponse

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        headers = {
            'X-Cache-Rule': 'foo',
            'X-Foo': 'bar',
            'ETag': '||blah||',
        }

        response.setHeader('X-Foo', 'baz')
        response.setHeader('X-Bar', 'qux')
        response.setStatus(200)

        body = cachedResponse(published, request, response, 404, headers, u"body")

        self.assertEqual(u"body", body)
        self.assertEqual(404, response.getStatus())
        self.assertEqual('foo', response.getHeader('X-Cache-Rule'))
        self.assertEqual('bar', response.getHeader('X-Foo'))
        self.assertEqual('qux', response.getHeader('X-Bar'))
        self.assertEqual('||blah||', response.getHeader('ETag', literal=1))

    def test_cachedResponse_gzip_off(self):
        from plone.app.caching.operations.utils import cachedResponse

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        headers = {
            'X-Cache-Rule': 'foo',
            'X-Foo': 'bar',
            'ETag': '||blah||',
        }

        response.setHeader('X-Foo', 'baz')
        response.setHeader('X-Bar', 'qux')
        response.setStatus(200)

        request.environ['HTTP_ACCEPT_ENCODING'] = 'gzip; deflate'
        response.enableHTTPCompression(request)

        assert response.enableHTTPCompression(query=True)

        body = cachedResponse(published, request, response, 404, headers, u"body", 0)

        self.assertEqual(u"body", body)
        self.assertEqual(404, response.getStatus())
        self.assertEqual('foo', response.getHeader('X-Cache-Rule'))
        self.assertEqual('bar', response.getHeader('X-Foo'))
        self.assertEqual('qux', response.getHeader('X-Bar'))
        self.assertEqual('||blah||', response.getHeader('ETag', literal=1))

        self.assertFalse(response.enableHTTPCompression(query=True))

    def test_cachedResponse_gzip_on(self):
        from plone.app.caching.operations.utils import cachedResponse

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        headers = {
            'X-Cache-Rule': 'foo',
            'X-Foo': 'bar',
            'ETag': '||blah||',
        }

        response.setHeader('X-Foo', 'baz')
        response.setHeader('X-Bar', 'qux')
        response.setStatus(200)

        request.environ['HTTP_ACCEPT_ENCODING'] = 'gzip; deflate'
        response.enableHTTPCompression(request, disable=True)

        assert not response.enableHTTPCompression(query=True)

        body = cachedResponse(published, request, response, 404, headers, u"body", 1)

        self.assertEqual(u"body", body)
        self.assertEqual(404, response.getStatus())
        self.assertEqual('foo', response.getHeader('X-Cache-Rule'))
        self.assertEqual('bar', response.getHeader('X-Foo'))
        self.assertEqual('qux', response.getHeader('X-Bar'))
        self.assertEqual('||blah||', response.getHeader('ETag', literal=1))

        self.assertTrue(response.enableHTTPCompression(query=True))

    # notModified()

    def test_notModified_minimal(self):
        from plone.app.caching.operations.utils import notModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        response.setStatus(200)

        body = notModified(published, request, response)

        self.assertEqual(u"", body)
        self.assertEqual(304, response.getStatus())

    def test_notModified_full(self):
        from plone.app.caching.operations.utils import notModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        response.setStatus(200)

        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"

        body = notModified(published, request, response, etag=etag, lastModified=now)

        self.assertEqual(u"", body)
        self.assertEqual(etag, response.getHeader('ETag', literal=1))
        self.assertEqual(None, response.getHeader('Last-Modified'))
        self.assertEqual(None, response.getHeader('Expires'))
        self.assertEqual(None, response.getHeader('Cache-Control'))
        self.assertEqual(304, response.getStatus())

class CacheCheckHelpersTest(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)

    # isModified()

    def test_isModified_no_headers_no_keys(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        self.assertEqual(True, isModified(request))

    def test_isModified_no_headers_with_keys(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        etag = '|foo'
        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(True, isModified(request, etag=etag, lastModified=lastModified))

    def test_isModified_ims_invalid_date(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'blah'

        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(True, isModified(request, lastModified=lastModified))

    def test_isModified_ims_modified(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Tue, 24 Nov 2009 03:04:05 GMT'

        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(True, isModified(request, lastModified=lastModified))

    def test_isModified_ims_not_modified(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Thu, 24 Nov 2011 03:04:05 GMT'

        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(False, isModified(request, lastModified=lastModified))

    def test_isModified_ims_not_modified_two_dates(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Thu, 24 Nov 2011 03:04:05 GMT; Thu, 24 Nov 2011 03:04:05'

        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(False, isModified(request, lastModified=lastModified))

    def test_isModified_ims_not_modified_etag_no_inm_header(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Thu, 24 Nov 2011 03:04:05 GMT'

        etag = '|foo'
        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(True, isModified(request, etag=etag, lastModified=lastModified))

    def test_isModified_inm_no_tags(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        etag = '|foo'

        self.assertEqual(True, isModified(request, etag=etag))

    def test_isModified_inm_one_tag_no_match(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|bar"'

        etag = '|foo'

        self.assertEqual(True, isModified(request, etag=etag))

    def test_isModified_inm_multiple_tags_no_match(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|bar", W/"|baz"'

        etag = '|foo'

        self.assertEqual(True, isModified(request, etag=etag))

    def test_isModified_inm_invalid_tag(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"'

        etag = '|foo'

        self.assertEqual(True, isModified(request, etag=etag))

    def test_isModified_inm_star(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"*", W/"|baz"'

        etag = '|foo'

        self.assertEqual(False, isModified(request, etag=etag))

    def test_isModified_inm_match_single(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|foo"'

        etag = '|foo'

        self.assertEqual(False, isModified(request, etag=etag))

    def test_isModified_inm_match_update(self):
        """
        If a site was previously configured to use etags and then the
        configuration updates, cached pages from the previous config
        will send and If-None-Match but will have no site configuration
        for etags. In this case, modified should return True since the
        headers need to be updated with the new config. Additionally,
        last modified may be attached to the request header, but
        If-None-Match always takes precedence over these headers and
        therefor they should be ignored.
        """
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        # at some point the code added dummy timestamps to this header
        request.environ['HTTP_IF_NONE_MATCH'] = '"1232342354.65"'

        etag = None

        self.assertEqual(True, isModified(request, etag=etag,
                                           lastModified='doesnt_really_matter'))


    def test_isModified_inm_match_multiple(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|foo", "|bar"'

        etag = '|foo'

        self.assertEqual(False, isModified(request, etag=etag))

    def test_isModified_inm_match_weak(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = 'W/"|foo"'

        etag = '|foo'

        self.assertEqual(False, isModified(request, etag=etag))

    def test_isModified_inm_match_ignores_ims_if_no_last_modified_date(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|foo"'
        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Tue, 24 Nov 2009 03:04:05 GMT'

        etag = '|foo'

        self.assertEqual(False, isModified(request, etag=etag))

    def test_isModified_inm_match_modified(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|foo"'
        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Tue, 24 Nov 2009 03:04:05 GMT'

        etag = '|foo'
        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(True, isModified(request, etag=etag, lastModified=lastModified))

    def test_isModified_inm_match_not_modified(self):
        from plone.app.caching.operations.utils import isModified

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_IF_NONE_MATCH'] = '"|foo"'
        request.environ['HTTP_IF_MODIFIED_SINCE'] = 'Thu, 24 Nov 2011 03:04:05 GMT'

        etag = '|foo'
        lastModified = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        self.assertEqual(False, isModified(request, etag=etag, lastModified=lastModified))

    # visibleToRole()

    def test_visibleToRole_not_real(self):
        from plone.app.caching.operations.utils import visibleToRole
        published = DummyPublished()
        self.assertEqual(False, visibleToRole(published, role='Anonymous'))

    def test_visibleToRole_permission(self):
        from plone.app.caching.operations.utils import visibleToRole

        s = SimpleItem()

        s.manage_permission('View', ('Member', 'Manager',))
        self.assertEqual(False, visibleToRole(s, role='Anonymous'))

        s.manage_permission('View', ('Member', 'Manager', 'Anonymous',))
        self.assertEqual(True, visibleToRole(s, role='Anonymous'))


class MiscHelpersTest(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)

    # getContext()

    def test_getContext(self):
        from plone.app.caching.operations.utils import getContext

        class Parent(object):
            implements(IContentish)

        parent = Parent()
        published = DummyPublished(parent)

        self.assertTrue(getContext(parent) is parent)
        self.assertTrue(getContext(published) is parent)

    def test_getContext_custom_marker(self):
        from plone.app.caching.operations.utils import getContext

        class Parent(object):
            implements(IContentish)

            def __init__(self, parent=None):
                self.__parent__ = parent

        class IDummy(Interface):
            pass

        grandparent = Parent()
        parent = Parent(grandparent)
        published = DummyPublished(parent)

        self.assertTrue(getContext(published, marker=IDummy) is None)
        self.assertTrue(getContext(published, marker=(IDummy,)) is None)

        alsoProvides(grandparent, IDummy)

        self.assertTrue(getContext(parent, marker=IDummy) is grandparent)
        self.assertTrue(getContext(published, marker=(IDummy,)) is grandparent)

    # formatDateTime()

    def test_formatDateTime_utc(self):
        from plone.app.caching.operations.utils import formatDateTime

        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())
        self.assertEqual('Wed, 24 Nov 2010 03:04:05 GMT', formatDateTime(dt))

    def test_formatDateTime_local(self):
        from plone.app.caching.operations.utils import formatDateTime

        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzlocal())
        inGMT = formatDateTime(dt)

        # Who knows what your local timezone is :-)
        self.assertTrue(inGMT.endswith(' GMT'))
        self.assertTrue('Nov 2010' in inGMT)

        # We lose microseconds. Big whoop.
        p = dateutil.parser.parse(inGMT).astimezone(dateutil.tz.tzlocal())
        lofi = datetime.datetime(2010, 11, 24, 3, 4, 5, 0, dateutil.tz.tzlocal())
        self.assertEqual(p, lofi)

    def test_formatDateTime_naive(self):
        from plone.app.caching.operations.utils import formatDateTime

        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 6)
        inGMT = formatDateTime(dt)

        # Who knows what your local timezone is :-)
        self.assertTrue(inGMT.endswith(' GMT'))
        self.assertTrue('Nov 2010' in inGMT)

        # Can't compare offset aware and naive
        p = dateutil.parser.parse(inGMT).astimezone(dateutil.tz.tzlocal())
        self.assertEqual((2010, 11, 24, 3, 4, 5), (p.year, p.month, p.day, p.hour, p.minute, p.second))

    # parseDateTime()

    def test_parseDateTime_invalid(self):
        from plone.app.caching.operations.utils import parseDateTime

        self.assertEqual(None, parseDateTime("foo"))

    def test_parseDateTime_rfc1123(self):
        from plone.app.caching.operations.utils import parseDateTime

        dt = datetime.datetime(2010, 11, 23, 3, 4, 5, 0, dateutil.tz.tzutc())
        self.assertEqual(dt, parseDateTime("'Tue, 23 Nov 2010 3:04:05 GMT'"))

    def test_formatDateTime_no_timezone(self):
        from plone.app.caching.operations.utils import parseDateTime

        # parser will assume input was local time
        dt = datetime.datetime(2010, 11, 23, 19, 4, 5, 0, dateutil.tz.tzlocal())
        self.assertEqual(dt, parseDateTime("'Tue, 23 Nov 2010 19:04:05'"))

    # getLastModified()

    def test_getLastModified_no_adaper(self):
        from plone.app.caching.operations.utils import getLastModified

        published = DummyPublished()
        self.assertEqual(None, getLastModified(published))

    def test_getLastModified_none(self):
        from plone.app.caching.operations.utils import getLastModified

        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return None

        provideAdapter(DummyLastModified)

        published = DummyPublished()
        self.assertEqual(None, getLastModified(published))

    def test_getLastModified_missing_timezone(self):
        from plone.app.caching.operations.utils import getLastModified

        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return datetime.datetime(2010, 11, 24, 3, 4, 5, 6)

        provideAdapter(DummyLastModified)

        published = DummyPublished()
        self.assertEqual(datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzlocal()),
                          getLastModified(published))

    def test_getLastModified_timezone(self):
        from plone.app.caching.operations.utils import getLastModified

        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())

        provideAdapter(DummyLastModified)

        published = DummyPublished()
        self.assertEqual(datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc()),
                          getLastModified(published))


    # getExpiration()

    def test_getExpiration_0(self):
        from plone.app.caching.operations.utils import getExpiration

        now = datetime.datetime.now()
        val = getExpiration(0)

        difference = now - val

        # it's more than a year in the past, which is plenty; it's actually
        # more like 10 years in the past, but it's hard to compare when the
        # calculation is based on the current time of the test.
        self.assertTrue(difference >= datetime.timedelta(days=365))

    def test_getExpiration_past(self):
        from plone.app.caching.operations.utils import getExpiration

        now = datetime.datetime.now()
        val = getExpiration(-1)

        difference = now - val

        # any value in the past basically has the same effect as setting -1
        self.assertTrue(difference >= datetime.timedelta(days=365))

    def test_getExpiration_future(self):
        from plone.app.caching.operations.utils import getExpiration

        now = datetime.datetime.now()
        val = getExpiration(60)

        difference = val - now

        # give the test two seconds' leeway
        self.assertTrue(difference >= datetime.timedelta(seconds=58))


    # getETag()

    def test_getETag_extra_only(self):
        from plone.app.caching.operations.utils import getETag

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        self.assertEqual('|foo|bar;baz', getETag(published, request, extraTokens=('foo', 'bar,baz')))

    def test_getETag_key_not_found(self):
        from plone.app.caching.operations.utils import getETag

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        self.assertEqual(None, getETag(published, request, keys=('foo', 'bar',)))

    def test_getETag_adapter_returns_none(self):
        from plone.app.caching.operations.utils import getETag
        from plone.app.caching.interfaces import IETagValue

        class FooETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def __call__(self):
                return 'foo'

        provideAdapter(FooETag, name=u"foo")

        class BarETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def __call__(self):
                return None

        provideAdapter(BarETag, name=u"bar")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        self.assertEqual('|foo|', getETag(published, request, keys=('foo', 'bar',)))

    def test_getETag_full(self):
        from plone.app.caching.operations.utils import getETag
        from plone.app.caching.interfaces import IETagValue

        class FooETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def __call__(self):
                return 'foo'

        provideAdapter(FooETag, name=u"foo")

        class BarETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def __call__(self):
                return 'bar'

        provideAdapter(BarETag, name=u"bar")

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()

        self.assertEqual('|foo|bar|baz;qux', getETag(published, request,
                keys=('foo', 'bar',), extraTokens=('baz,qux',)))


    # parseETags()

    def test_parseETags_empty(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual([], parseETags(''))

    def test_parseETags_None(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual([], parseETags(''))

    def test_parseETags_star(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['*'], parseETags('*'))

    def test_parseETags_star_quoted(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['*'], parseETags('"*"'))

    def test_parseETags_single(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz'], parseETags('|foo|bar;baz'))

    def test_parseETags_single_quoted(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz'], parseETags('"|foo|bar;baz"'))

    def test_parseETags_multiple(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz', '1234'], parseETags('|foo|bar;baz, 1234'))

    def test_parseETags_multiple_quoted(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz', '1234'], parseETags('"|foo|bar;baz", "1234"'))

    def test_parseETags_multiple_nospace(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz', '1234'], parseETags('|foo|bar;baz,1234'))

    def test_parseETags_multiple_quoted_nospace(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz', '1234'], parseETags('"|foo|bar;baz","1234"'))

    def test_parseETags_multiple_weak(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz', '1234'], parseETags('|foo|bar;baz, W/1234'))

    def test_parseETags_multiple_quoted_weak(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz', '1234'], parseETags('"|foo|bar;baz", W/"1234"'))

    def test_parseETags_multiple_weak_disallowed(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz'], parseETags('|foo|bar;baz, W/1234', allowWeak=False))

    def test_parseETags_multiple_quoted_weak_disallowed(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEqual(['|foo|bar;baz'], parseETags('"|foo|bar;baz", W/"1234"', allowWeak=False))

class RAMCacheTest(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)

    # getRAMCache()

    def test_getRAMCache_no_chooser(self):
        from plone.app.caching.operations.utils import getRAMCache
        self.assertEqual(None, getRAMCache())

    def test_getRAMCache_custom_global_key(self):
        from plone.app.caching.operations.utils import getRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'foo'
                return cache

        provideUtility(Chooser())
        self.assertEqual(cache, getRAMCache('foo'))

    def test_getRAMCache_normal(self):
        from plone.app.caching.operations.utils import getRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())
        self.assertEqual(cache, getRAMCache())


    # getRAMCacheKey()

    def test_getRAMCacheKey_empty(self):
        from plone.app.caching.operations.utils import getRAMCacheKey

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        self.assertEqual('http://example.com?', getRAMCacheKey(request))

    def test_getRAMCacheKey_normal(self):
        from plone.app.caching.operations.utils import getRAMCacheKey

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = 'x=1&y=2'

        self.assertEqual('http://example.com/foo/bar?x=1&y=2', getRAMCacheKey(request))

    def test_getRAMCacheKey_etag(self):
        from plone.app.caching.operations.utils import getRAMCacheKey

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = 'x=1&y=2'

        self.assertEqual('||foo|bar||http://example.com/foo/bar?x=1&y=2', getRAMCacheKey(request, etag="|foo|bar"))


    # storeResponseInRAMCache()

    def test_storeResponseInRAMCache_no_key(self):
        from plone.app.caching.operations.utils import storeResponseInRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        result = u"Body"
        response.setHeader('X-Foo', 'bar')

        storeResponseInRAMCache(request, response, result)

        self.assertEqual(0, len(cache))

    def test_storeResponseInRAMCache_no_cache(self):
        from plone.app.caching.operations.utils import storeResponseInRAMCache

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        result = u"Body"
        response.setHeader('X-Foo', 'bar')

        IAnnotations(request)['plone.app.caching.operations.ramcache.key'] = 'foo'

        storeResponseInRAMCache(request, response, result)

    def test_storeResponseInRAMCache_normal(self):
        from plone.app.caching.operations.utils import storeResponseInRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        result = u"Body"
        response.setHeader('X-Foo', 'bar')

        IAnnotations(request)['plone.app.caching.operations.ramcache.key'] = 'foo'

        storeResponseInRAMCache(request, response, result)

        self.assertEqual(1, len(cache))
        cached = normalize_response_cache(cache['foo'])
        self.assertEqual((200, {'x-foo': 'bar'}, u'Body', 0), cached)

    def test_storeResponseInRAMCache_gzip(self):
        from plone.app.caching.operations.utils import storeResponseInRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['HTTP_ACCEPT_ENCODING'] = 'gzip; deflate'
        response.enableHTTPCompression(request)

        result = u"Body"
        response.setHeader('X-Foo', 'bar')

        IAnnotations(request)['plone.app.caching.operations.ramcache.key'] = 'foo'

        storeResponseInRAMCache(request, response, result)

        self.assertEqual(1, len(cache))
        cached = normalize_response_cache(cache['foo'])
        self.assertEqual((200, {'x-foo': 'bar'}, u'Body', 1), cached)

    def test_storeResponseInRAMCache_custom_keys(self):
        from plone.app.caching.operations.utils import storeResponseInRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'cachekey'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        result = u"Body"
        response.setHeader('X-Foo', 'bar')

        IAnnotations(request)['annkey'] = 'foo'

        storeResponseInRAMCache(request, response, result, globalKey='cachekey', annotationsKey='annkey')

        self.assertEqual(1, len(cache))
        cached = normalize_response_cache(cache['foo'])
        self.assertEqual((200, {'x-foo': 'bar'}, u'Body', 0), cached)

    # fetchFromRAMCache()

    def test_fetchFromRAMCache_no_cache(self):
        from plone.app.caching.operations.utils import fetchFromRAMCache

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = ''

        self.assertEqual(None, fetchFromRAMCache(request))

    def test_fetchFromRAMCache_minimal(self):
        from plone.app.caching.operations.utils import fetchFromRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = ''

        cache['http://example.com/foo/bar?'] = (200, {'x-foo': 'bar'}, u'Body')

        cached = normalize_response_cache(fetchFromRAMCache(request))
        self.assertEqual((200, {'x-foo': 'bar'}, u'Body'), cached)

    def test_fetchFromRAMCache_with_etag(self):
        from plone.app.caching.operations.utils import fetchFromRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = ''

        cache['||a|b||http://example.com/foo/bar?'] = (200, {'x-foo': 'bar'}, u'Body')

        cached = normalize_response_cache(fetchFromRAMCache(request, etag="|a|b"))
        self.assertEqual((200, {'x-foo': 'bar'}, u'Body'), cached)

    def test_fetchFromRAMCache_custom_key(self):
        from plone.app.caching.operations.utils import fetchFromRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'cachekey'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = ''

        cache['http://example.com/foo/bar?'] = (200, {'x-foo': 'bar'}, u'Body')

        cached = normalize_response_cache(fetchFromRAMCache(request, globalKey='cachekey'))
        self.assertEqual((200, {'x-foo': 'bar'}, u'Body'), cached)

    def test_fetchFromRAMCache_miss(self):
        from plone.app.caching.operations.utils import fetchFromRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = ''

        cache['http://example.com/foo/bar?'] = (200, {'x-foo': 'bar'}, u'Body')

        cached = normalize_response_cache(fetchFromRAMCache(request, etag='|foo'))
        self.assertEqual(None, cached)

    def test_fetchFromRAMCache_miss_custom_default(self):
        from plone.app.caching.operations.utils import fetchFromRAMCache

        class Cache(dict):
            pass

        cache = Cache()

        class Chooser(object):
            implements(ICacheChooser)

            def __call__(self, key):
                assert key == 'plone.app.caching.operations.ramcache'
                return cache

        provideUtility(Chooser())

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)

        request.environ['PATH_INFO'] = '/foo/bar'
        request.environ['QUERY_STRING'] = ''

        cache['http://example.com/foo/bar?'] = (200, {'x-foo': 'bar'}, u'Body')

        marker = object()
        cached = normalize_response_cache(fetchFromRAMCache(request, etag='|foo', default=marker))
        self.assertTrue(cached is marker)
