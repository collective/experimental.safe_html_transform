from Products.Archetypes.utils import shasattr
from Products.CMFCore.utils import getToolByName
from Testing import ZopeTestCase
from sets import Set
from wicked import utils
from wicked.interfaces import IWickedFilter, ICacheManager, IUID
from wickedtestcase import WickedTestCase
import os, sys, time
import traceback
import unittest
import pdb; st = pdb.set_trace

MARKER = dict(path='/apath',
              icon='anicon.ico',
              uid='uid')

class TestLinkCache(WickedTestCase):
    wicked_type = 'IronicWiki'
    wicked_field = 'body'

    def afterSetUp(self):
        """
        sets the body of page1 to be a wicked link of the id of page2
        """
        super(TestLinkCache, self).afterSetUp()
        field = self.page1.getField(self.wicked_field)
        field.set(self.page1, "((%s))" % self.page2.Title())
        self.field = field
        self.filter = utils.getWicked(field, self.page1)
        self.wicked_ccm = self.filter.cache
        self.wicked_ccm.name=field.getName()

    def test_linkGetsCached(self):
        field = self.field
        wicked_ccm = self.wicked_ccm
        pg2_id = self.page2.getId()
        val = wicked_ccm.get(pg2_id)
        self.failUnless(val)
        data=dict(path='/plone/Members/test_user_1_/dmv-computer-has-died',
                  icon='plone/document_icon.gif')
        data['uid']=IUID(self.page2)
        self.failUnlessEqual(set([i['uid'] for i in val]),
                             set([data['uid']]))

    def test_cacheIsUsed(self):
        field = self.field
        wicked_ccm = self.wicked_ccm
        pg2_id = self.page2.getId()
        wicked_ccm.set((pg2_id, IUID(self.page2)), [MARKER])
        value = self.getRenderedWickedField(self.page1)
        self.failUnless(MARKER['path'] in value)
        self.failIfWickedLink(self.page1, self.page2)


def test_suite():
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import ZopeDocTestSuite
    suite.addTest(unittest.makeSuite(TestLinkCache))
    return suite

