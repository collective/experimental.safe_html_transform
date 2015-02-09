import pkg_resources

import unittest2 as unittest

from plone.testing.z2 import Browser

from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, TEST_USER_PASSWORD
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.app.testing import setRoles
from plone.app.testing import applyProfile

from cStringIO import StringIO

import datetime
import dateutil.parser
import dateutil.tz

import OFS.Image
from Products.CMFCore.utils import getToolByName

from zope.component import getUtility

from zope.globalrequest import setRequest

from plone.registry.interfaces import IRegistry
from plone.caching.interfaces import ICacheSettings
from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurger
from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.testing import PLONE_APP_CACHING_FUNCTIONAL_TESTING

TEST_IMAGE = pkg_resources.resource_filename('plone.app.caching.tests', 'test.gif')
TEST_FILE = pkg_resources.resource_filename('plone.app.caching.tests', 'test.gif')


class TestProfileWithCaching(unittest.TestCase):
    """This test aims to exercise the caching operations expected from the
    `with-caching-proxy` profile.

    Several of the operations are just duplicates of the ones for the
    `without-caching-proxy` profile but we still want to redo them in this
    context to ensure the profile has set the correct settings.
    """

    layer = PLONE_APP_CACHING_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']

        setRequest(self.portal.REQUEST)

        applyProfile(self.portal, 'plone.app.caching:with-caching-proxy')

        self.registry = getUtility(IRegistry)

        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cachePurgingSettings = self.registry.forInterface(ICachePurgingSettings)
        self.ploneCacheSettings = self.registry.forInterface(IPloneCacheSettings)

        self.cacheSettings.enabled = True

        self.purger = getUtility(IPurger)
        self.purger.reset()

    def tearDown(self):
        setRequest(None)

    def test_composite_views(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?

        catalog = self.portal['portal_catalog']

        # Add folder content
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()

        # Add page content
        self.portal['f1'].invokeFactory('Document', 'd1')
        self.portal['f1']['d1'].setTitle(u"Document one")
        self.portal['f1']['d1'].setDescription(u"Document one description")
        testText = "Testing... body one"
        self.portal['f1']['d1'].setText(testText)
        self.portal['f1']['d1'].reindexObject()

        # Publish the folder and page
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        self.portal.portal_workflow.doActionFor(self.portal['f1']['d1'], 'publish')

        # Should we set up the etag components?
        # - set member?  No
        # - reset catalog counter?  Maybe
        # - set server language?
        # - turn on gzip?
        # - set skin?  Maybe
        # - leave status unlocked
        #

        import transaction; transaction.commit()

        # Request the authenticated folder
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.open(self.portal['f1'].absolute_url())
        self.assertEqual('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        #self.assertEqual('"|test_user_1_|50|en|0|Sunburst Theme|0', browser.headers['ETag'])
        self.assertEqual('"|test_user_1_|%d|en|0|Sunburst Theme|0|0|' % catalog.getCounter(), browser.headers['ETag'][:42])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Set the copy/cut cookie and then request the folder view again
        browser.cookies.create('__cp', 'xxx')
        browser.open(self.portal['f1'].absolute_url())
        # The response should be the same as before except for the etag
        self.assertEqual('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEqual('"|test_user_1_|%d|en|0|Sunburst Theme|0|1|' % catalog.getCounter(), browser.headers['ETag'][:42])

        # Request the authenticated page
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertTrue(testText in browser.contents)
        self.assertEqual('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        #self.assertEqual('"|test_user_1_|50|en|0|Sunburst Theme|0', browser.headers['ETag'])
        self.assertEqual('"|test_user_1_|%d|en|0|Sunburst Theme|0' % catalog.getCounter(), browser.headers['ETag'][:39])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the authenticated page again -- to test RAM cache.
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEqual('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # Authenticated should NOT be RAM cached
        self.assertEqual(None, browser.headers.get('X-RAMCache'))

        # Request the authenticated page again -- with an INM header to test 304
        etag = browser.headers['ETag']
        browser = Browser(self.app)
        browser.raiseHttpErrors = False  # we really do want to see the 304
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal['f1']['d1'].absolute_url())
        # This should be a 304 response
        self.assertEqual('304 Not Modified', browser.headers['Status'])
        self.assertEqual('', browser.contents)

        # Request the anonymous folder
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal['f1'].absolute_url())
        self.assertEqual('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        #self.assertEqual('"||50|en|0|Sunburst Theme|0|', browser.headers['ETag'])
        self.assertEqual('"||%d|en|0|Sunburst Theme|0|' % catalog.getCounter(), browser.headers['ETag'][:28])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the anonymous page
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEqual('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        self.assertTrue(testText in browser.contents)
        # This should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        #self.assertEqual('"||50|en|0|Sunburst Theme|0|', browser.headers['ETag'])
        self.assertEqual('"||%d|en|0|Sunburst Theme|0|' % catalog.getCounter(), browser.headers['ETag'][:28])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the anonymous page again -- to test RAM cache.
        # Anonymous should be RAM cached
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEqual('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should come from RAM cache
        self.assertEqual('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.assertTrue(testText in browser.contents)
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        #self.assertEqual('"||50|en|0|Sunburst Theme|0|', browser.headers['ETag'])
        self.assertEqual('"||%d|en|0|Sunburst Theme|0|' % catalog.getCounter(), browser.headers['ETag'][:28])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the anonymous page again -- with an INM header to test 304.
        etag = browser.headers['ETag']
        browser = Browser(self.app)
        browser.raiseHttpErrors = False
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEqual('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEqual('304 Not Modified', browser.headers['Status'])
        self.assertEqual('', browser.contents)

        # Edit the page to update the etag
        testText2 = "Testing... body two"
        self.portal['f1']['d1'].setText(testText2)
        self.portal['f1']['d1'].reindexObject()

        import transaction; transaction.commit()

        # Request the anonymous page again -- to test expiration of 304 and RAM.
        etag = browser.headers['ETag']
        browser = Browser(self.app)
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEqual('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # The etag has changed so we should get a fresh page.
        self.assertEqual(None, browser.headers.get('X-RAMCache'))
        self.assertEqual('200 Ok', browser.headers['Status'])

    def test_content_feeds(self):

        catalog = self.portal['portal_catalog']

        # Enable syndication
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.syndication = getToolByName(self.portal, 'portal_syndication')
        self.syndication.editProperties(isAllowed=True)
        self.syndication.enableSyndication(self.portal)

        import transaction; transaction.commit()

        # Request the rss feed
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEqual('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInProxy
        self.assertEqual('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertEqual('"||%d|en|0|Sunburst Theme"' % catalog.getCounter(), browser.headers['ETag'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the rss feed again -- to test RAM cache
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        rssText = browser.contents
        browser = Browser(self.app)
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEqual('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should come from the RAM cache
        self.assertEqual('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.assertEqual(rssText, browser.contents)
        self.assertEqual('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertEqual('"||%d|en|0|Sunburst Theme"' % catalog.getCounter(), browser.headers['ETag'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the rss feed again -- with an INM header to test 304.
        etag = browser.headers['ETag']
        browser = Browser(self.app)
        browser.raiseHttpErrors = False
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEqual('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEqual('304 Not Modified', browser.headers['Status'])
        self.assertEqual('', browser.contents)

        # Request the authenticated rss feed
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEqual('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEqual('"|test_user_1_|%d|en|0|Sunburst Theme"' % catalog.getCounter(), browser.headers['ETag'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the authenticated rss feed again -- to test RAM cache
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEqual('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Authenticated should NOT be RAM cached
        self.assertEqual(None, browser.headers.get('X-RAMCache'))

    def test_content_files(self):

        # Add folder content
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()

        # Add content image
        self.portal['f1'].invokeFactory('Image', 'i1')
        self.portal['f1']['i1'].setTitle(u"Image one")
        self.portal['f1']['i1'].setDescription(u"Image one description")
        self.portal['f1']['i1'].setImage(OFS.Image.Image('test.gif', 'test.gif', open(TEST_IMAGE, 'rb')))
        self.portal['f1']['i1'].reindexObject()

        import transaction; transaction.commit()

        # Request the image with Manager role
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,))
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEqual('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Folder not published yet so image should not be cached in proxy
        # so this should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEqual('---lastmodified---', browser.headers['Last-Modified'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request an image scale with Manager role
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,))
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEqual('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Folder not published yet so image scale should not be cached in proxy
        # so this should use cacheInBrowser
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEqual('---lastmodified---', browser.headers['Last-Modified'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Publish the folder
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')

        import transaction; transaction.commit()

        # Request the image
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEqual('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Now visible to anonymous so this should use cacheInProxy
        self.assertEqual('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEqual('---lastmodified---', browser.headers['Last-Modified'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

        # Request the image again -- with an IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser(self.app)
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEqual('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEqual('304 Not Modified', browser.headers['Status'])
        self.assertEqual('', browser.contents)

        # Request an image scale
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEqual('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Now visible to anonymous so this should use cacheInProxy
        self.assertEqual('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEqual('---lastmodified---', browser.headers['Last-Modified'])
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))

    def test_resources(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?

        import transaction; transaction.commit()

        # Request a skin image
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(self.portal.absolute_url() + '/rss.png')
        self.assertEqual('plone.resource', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEqual('max-age=86400, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEqual('---lastmodified---', browser.headers['Last-Modified'])
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.assertTrue(timedelta > datetime.timedelta(seconds=86390))

        # Request the skin image again -- with an IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser(self.app)
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(self.portal.absolute_url() + '/rss.png')
        self.assertEqual('plone.resource', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEqual('304 Not Modified', browser.headers['Status'])
        self.assertEqual('', browser.contents)

        # Request a large datafile (over 64K) to test files that use
        # the "response.write()" function to initiate a streamed response.
        # This is of type OFS.Image.File but it should also apply to
        # large OFS.Image.Image, large non-blog ATImages/ATFiles, and
        # large Resource Registry cooked files, which all use the same
        # method to initiate a streamed response.
        s = "a" * (1 << 16) * 3
        self.portal.manage_addFile('bigfile', file=StringIO(s), content_type='application/octet-stream')

        import transaction; transaction.commit()

        browser = Browser(self.app)
        browser.open(self.portal['bigfile'].absolute_url())
        self.assertEqual('plone.resource', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEqual('max-age=86400, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEqual('---lastmodified---', browser.headers['Last-Modified'])
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.assertTrue(timedelta > datetime.timedelta(seconds=86390))

    def test_stable_resources(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?
        # (yes, this is not really testing anything. It's a placeholder)
        #
        # We don't actually have any non-RR stable resources yet
        # What is the best way to test this?
        # Maybe not important since the RR test exercises the same code?
        pass

    def test_stable_resources_resource_registries(self):

        cssregistry = self.portal.portal_css
        # Cook resources to update bundles for theme.
        cssregistry.cookResources()
        import transaction; transaction.commit()

        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?

        # Request a ResourceRegistry resource
        path = cssregistry.absolute_url() + "/Sunburst%20Theme/public.css"
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser(self.app)
        browser.open(path)
        self.assertEqual('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEqual('max-age=31536000, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.assertFalse(None == browser.headers.get('Last-Modified'))
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.assertTrue(timedelta > datetime.timedelta(seconds=31535990))

        # Request the ResourceRegistry resource again -- with IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser(self.app)
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(path)
        self.assertEqual('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        self.assertEqual('304 Not Modified', browser.headers['Status'])
        self.assertEqual('', browser.contents)
        self.assertEqual(None, browser.headers.get('Last-Modified'))
        self.assertEqual(None, browser.headers.get('Expires'))
        self.assertEqual(None, browser.headers.get('Cache-Control'))

        # Request the ResourceRegistry resource -- with RR in debug mode
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        cssregistry.setDebugMode(True)

        transaction.commit()

        browser = Browser(self.app)
        browser.open(path)
        self.assertEqual('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEqual('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use doNotCache
        self.assertEqual('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEqual(None, browser.headers.get('Last-Modified'))
        self.assertTrue(now > dateutil.parser.parse(browser.headers['Expires']))
