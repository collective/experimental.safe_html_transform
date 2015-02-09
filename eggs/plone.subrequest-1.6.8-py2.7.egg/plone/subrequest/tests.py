import manuel.doctest
import manuel.testcase
import manuel.testing
import unittest2 as unittest

from plone.subrequest import subrequest
from plone.subrequest.testing import INTEGRATION_TESTING, FUNCTIONAL_TESTING
from plone.testing import z2
from zope.globalrequest import getRequest
from zope.site.hooks import getSite

def traverse(url):
    request = getRequest()
    traversed = request.traverse(url)
    request.processInputs()
    request['PATH_INFO'] = url
    return request


class FunctionalTests(unittest.TestCase):
    layer = FUNCTIONAL_TESTING

    def setUp(self):
        self.browser = z2.Browser(self.layer['app'])

    def test_absolute(self):
        self.browser.open('http://nohost/folder1/@@url')
        self.assertEqual(self.browser.contents, 'http://nohost/folder1')

    def test_virtual_hosting(self):
        parts = ('folder1', 'folder1A/@@url')
        expect = 'folder1A'
        url = "http://nohost/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % parts
        expect_url = 'http://example.org/fizz/buzz/fizzbuzz/%s' % expect
        self.browser.open(url)
        self.assertEqual(self.browser.contents, expect_url)

    def test_virtual_hosting_relative(self):
        parts = ('folder1', 'folder1A?url=folder1Ai/@@url')
        expect = 'folder1A/folder1Ai'
        url = "http://nohost/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % parts
        expect_url = 'http://example.org/fizz/buzz/fizzbuzz/%s' % expect
        self.browser.open(url)
        self.assertEqual(self.browser.contents, expect_url)

    def test_virtual_hosting_absolute(self):
        parts = ('folder1', 'folder1A?url=/folder1B/@@url')
        expect = 'folder1B'
        url = "http://nohost/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % parts
        expect_url = 'http://example.org/fizz/buzz/fizzbuzz/%s' % expect
        self.browser.open(url)
        self.assertEqual(self.browser.contents, expect_url)


class IntegrationTests(unittest.TestCase):
    layer = INTEGRATION_TESTING

    def test_absolute(self):
        response = subrequest('/folder1/@@url')
        self.assertEqual(response.body, 'http://nohost/folder1')

    def test_absolute_query(self):
        response = subrequest('/folder1/folder1A?url=/folder2/folder2A/@@url')
        self.assertEqual(response.body, 'http://nohost/folder2/folder2A')

    def test_relative(self):
        response = subrequest('/folder1?url=folder1B/@@url')
        # /folder1 resolves to /folder1/@@test
        self.assertEqual(response.body, 'http://nohost/folder1/folder1B')

    def test_root(self):
        response = subrequest('/')
        self.assertEqual(response.body, 'Root: http://nohost')

    def test_virtual_hosting(self):
        url = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % ('folder1', 'folder1A/@@url')
        response = subrequest(url)
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1A')

    def test_virtual_hosting_unicode(self):
        url = u"/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % ('folder1', 'folder1A/@@url')
        response = subrequest(url)
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1A')

    def test_virtual_hosting_relative(self):
        url = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % ('folder1', 'folder1A?url=folder1B/@@url')
        response = subrequest(url)
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1B')

    def test_not_found(self):
        response = subrequest('/notfound')
        self.assertEqual(response.status, 404)

    def test_virtual_host_root(self):
        parts = ('folder1', 'folder1A/@@url')
        url = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % parts
        traverse(url)
        response = subrequest('/folder1B/@@url')
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1B')

    def test_virtual_host_root_with_root(self):
        parts = ('folder1', 'folder1A/@@url')
        url = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/%s" % parts
        traverse(url)
        app = self.layer['app']
        response = subrequest('/folder1Ai/@@url', root=app.folder1.folder1A)
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1A/folder1Ai')

    def test_virtual_host_space(self):
        parts = ('folder2', 'folder2A/folder2Ai space/@@url')
        url = "/VirtualHostBase/http/example.org:80/%s/VirtualHostRoot/%s" % parts
        traverse(url)
        app = self.layer['app']
        response = subrequest('/folder2A/@@url', root=app.folder2)
        self.assertEqual(response.body, 'http://example.org/folder2A')

    def test_virtual_host_root_at_root(self):
        url = "/VirtualHostBase/http/example.org:80/folder1/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz"
        traverse(url)
        response = subrequest('/folder1B/@@url')
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1B')

    def test_virtual_host_root_at_root_trailing(self):
        url = "/VirtualHostBase/http/example.org:80/folder1/VirtualHostRoot/_vh_fizz/_vh_buzz/_vh_fizzbuzz/"
        traverse(url)
        response = subrequest('/folder1B/@@url')
        self.assertEqual(response.body, 'http://example.org/fizz/buzz/fizzbuzz/folder1B')

    def test_virtual_host_with_root_double_slash(self):
        url = "/VirtualHostBase/http/example.org:80/VirtualHostRoot/_vh_fizz/folder1/folder2//folder2A"
        traverse(url)
        root = self.layer['app'].folder1
        response = subrequest('/folder1B/@@url', root=root)
        self.assertEqual(response.body, 'http://example.org/fizz/folder1/folder1B')

    def test_subrequest_root(self):
        app = self.layer['app']
        response = subrequest('/folder1Ai/@@url', root=app.folder1.folder1A)
        self.assertEqual(response.body, 'http://nohost/folder1/folder1A/folder1Ai')

    def test_site(self):
        app = self.layer['app']
        traverse('/folder1')
        site_url1 = getSite().absolute_url()
        response = subrequest('/folder2/@@url')
        self.assertEqual(response.status, 200)
        site_url2 = getSite().absolute_url()
        self.assertEqual(site_url1, site_url2)

    def test_parameter(self):
        response = subrequest('/folder1/@@parameter?foo=bar')
        self.assertTrue('foo' in response.body)

    def test_cookies(self):
        response = subrequest('/folder1/@@test?url=/folder1/cookie')
        self.assertTrue('cookie_name' in response.cookies)

    def test_stream_iterator(self):
        # Only a ZServerHTTPResponse is IStreamIterator Aware
        from ZServer.HTTPResponse import ZServerHTTPResponse
        request = getRequest()
        request.response.__class__ = ZServerHTTPResponse
        response = subrequest('/@@stream')
        self.assertEqual(response.getBody(), "hello")

    def test_filestream_iterator(self):
        # Only a ZServerHTTPResponse is IStreamIterator Aware
        from ZServer.HTTPResponse import ZServerHTTPResponse
        request = getRequest()
        request.response.__class__ = ZServerHTTPResponse
        response = subrequest('/@@filestream')
        from ZPublisher.Iterators import filestream_iterator
        self.assertTrue(isinstance(response.stdout, filestream_iterator))
        self.assertEqual(response.getBody(), "Test")

    def test_blobstream_iterator(self):
        # Only a ZServerHTTPResponse is IStreamIterator Aware
        from ZServer.HTTPResponse import ZServerHTTPResponse
        request = getRequest()
        request.response.__class__ = ZServerHTTPResponse
        response = subrequest('/@@blobstream')
        from ZODB.blob import BlobFile
        self.assertTrue(isinstance(response.stdout, BlobFile))
        self.assertEqual(response.getBody(), "Hi, Blob!")

    def test_other_variables(self):
        request = getRequest()
        request['foo'] = 'bar'
        request['VIRTUAL_URL'] = 'parent'
        request['URL9'] = 'parent'
        response = subrequest('/folder1/@@parameter')
        self.assertTrue("'foo'" in response.body)
        self.assertFalse("'URL9'" in response.body)
        self.assertFalse("'VIRTUAL_URL'" in response.body)


def test_suite():
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    m = manuel.doctest.Manuel()
    m += manuel.testcase.MarkerManuel()
    doctests = manuel.testing.TestSuite(m, 'usage.txt', globs=dict(subrequest=subrequest, traverse=traverse))
    # Set the layer on the manuel doctests for now
    for test in doctests:
        test.layer = INTEGRATION_TESTING
        test.globs['layer'] = INTEGRATION_TESTING
    suite.addTest(doctests)
    return suite
