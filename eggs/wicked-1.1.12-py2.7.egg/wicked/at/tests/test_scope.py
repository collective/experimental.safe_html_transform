import os, sys, time
import unittest
from sets import Set
import traceback

from Testing import ZopeTestCase

from wicked.normalize import titleToNormalizedId
from wicked.config import BACKLINK_RELATIONSHIP
from wicked.atcontent.ironicwiki import IronicWiki
from wickedtestcase import WickedTestCase, makeContent, WickedSite

from zope.component import adapter, provideAdapter
from zope.interface import implementer, Interface
from zope.interface import alsoProvides, noLongerProvides
from wicked.interfaces import IScope, IAmWicked, IAmWickedField

class IScopedField(IAmWickedField):
    """ scope marker """


@implementer(IScope)
@adapter(IScopedField, IAmWicked)
def scopeTester(field, context):
    """
    a demo scope function for testing, returns a scope that includes
    the parent of the current container, but not anything two levels
    (or more) up
    """
    scope_obj = context.aq_inner.aq_parent
    if not context.isPrincipiaFolderish:
        scope_obj = scope_obj.aq_inner.aq_parent
    path = '/'.join(scope_obj.getPhysicalPath())
    return path


class Scoped(WickedSite):

    @classmethod
    def setUp(cls):
        alsoProvides(IronicWiki.schema['body'], IScopedField)
        # @@ maybe make this local?
        provideAdapter(scopeTester)

    @classmethod
    def tearDown(cls):
        # clear out markers
        noLongerProvides(IronicWiki.schema['body'], IScopedField)


class TestWickedScope(WickedTestCase):
    wicked_type = 'IronicWiki'
    wicked_field = 'body'
    layer = Scoped

    def test_registration(self):
        # test our test ;)
        from zope.component import getMultiAdapter
        assert getMultiAdapter((IronicWiki.schema['body'], self.page1), IScope) \
               == '/plone/Members'

    def test_insideScope(self):
        # @@ this test passes without "scope". bogus?
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(f2, 'w1', 'IronicWiki',
                          title='W1 Title')

        self.set_text(w1, "((%s))" % self.page1.Title())
        self.failUnlessWickedLink(w1, self.page1)

    def test_outsideScope(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        f3 = makeContent(f2, 'f3', 'Folder')
        w1 = makeContent(f3, 'w1', 'IronicWiki',
                          title='W1 Title')
        self.set_text(w1, "((%s))" % self.page1.Title())
        self.failIfWickedLink(w1, self.page1)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWickedScope))
    return suite
