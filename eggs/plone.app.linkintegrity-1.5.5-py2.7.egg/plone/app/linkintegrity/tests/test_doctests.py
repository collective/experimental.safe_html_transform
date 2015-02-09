# -*- coding:utf-8 -*-
# setup tests with all doctests found in docs/

from plone.app.linkintegrity import docs
from plone.app.linkintegrity.tests import layer, utils
from plone.app.linkintegrity.parser import extractLinks
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.PloneTestCase import PloneTestCase
from unittest import TestSuite, TestCase, makeSuite
from os.path import join, split, abspath, dirname
from os import walk
from re import compile
from sys import argv


PloneTestCase.setupPloneSite()

from ZPublisher.HTTPRequest import HTTPRequest
set_orig = HTTPRequest.set

from zope.testing import doctest
OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


DATA = '''<a
        href="http://foo.com/@@v?Title=S\xc3\xa3o&amp;section=text">
        Foo</a>'''

EXPECTED = 'http://foo.com/@@v?Title=S\xc3\xa3o&section=text'.decode('utf-8')


class LinkIntegrityFunctionalTestCase(PloneTestCase.FunctionalTestCase):

    layer = layer.integrity

    def afterSetUp(self):
        """ create some sample content to test with """
        # HTTPRequest's 'set' function is set to it's original implementation
        # at the start of each new test, since otherwise the below monkey
        # patch will apply to all remaining tests (and break them);  see
        # comment below in 'disableEventCountHelper'
        HTTPRequest.set = set_orig

    def getBrowser(self, loggedIn=False):
        """ instantiate and return a testbrowser for convenience """
        return utils.getBrowser(loggedIn)

    def setStatusCode(self, key, value):
        from ZPublisher import HTTPResponse
        HTTPResponse.status_codes[key.lower()] = value

    def setText(self, obj, text, **kw):
        kw['text'] = '<html> <body> %s </body> </html>' % text
        return obj.processForm(values=kw)

    def disableEventCountHelper(self):
        # so here's yet another monkey patch ;), but only to avoid having
        # to change almost all the tests after introducing the setting of
        # the helper value in 'folder_delete', which prevents presenting
        # the user with multiple confirmation forms;  this patch prevents
        # setting the value and is meant to disable this optimization in
        # some of the tests written so far, thereby not invalidating them...
        def set(self, key, value, set_orig=set_orig):
            if key == 'link_integrity_events_to_expect':
                value = 0
            set_orig(self, key, value)
        HTTPRequest.set = set


class LinkIntegrityTestCase(TestCase):

    def testHandleParserException(self):
        self.assertEqual(extractLinks('<foo\'d>'), ())
        data = '<a href="http://foo.com">foo</a><bar\'d>'
        self.assertEqual(extractLinks(data), ('http://foo.com',))

    def testHandleStringEncodingException(self):
        expected = (EXPECTED,)
        self.assertEqual(extractLinks(DATA), expected)


# we check argv to enable testing of explicitely named doctests
if '-t' in argv:
    pattern = compile('.*\.(txt|rst)$')
else:
    pattern = compile('^test.*\.(txt|rst)$')


def test_suite():
    suite = TestSuite([
        makeSuite(LinkIntegrityTestCase),
    ])
    docs_dir = abspath(dirname(docs.__file__)) + '/'
    for path, dirs, files in walk(docs_dir):
        for name in files:
            relative = join(path, name)[len(docs_dir):]
            if not '.svn' in split(path) and pattern.search(name):
                suite.addTest(FunctionalDocFileSuite(relative,
                    optionflags=OPTIONFLAGS,
                    package=docs.__name__,
                    test_class=LinkIntegrityFunctionalTestCase))
    return suite
