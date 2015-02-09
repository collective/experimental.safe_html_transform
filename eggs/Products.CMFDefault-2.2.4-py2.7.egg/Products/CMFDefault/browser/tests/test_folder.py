##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Test Products.CMFDefault.browser.folder """

import unittest

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
from Testing import ZopeTestCase

from zope.component import getSiteManager
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces.browser import IBrowserPublisher

from Products.CMFCore.PortalFolder import PortalFolder
from Products.CMFCore.tests.base.dummy import DummySite, DummyTool
from Products.CMFCore.tests.base.dummy import DummyUserFolder, DummyContent
from Products.CMFCore.interfaces import IPropertiesTool

from Products.CMFDefault.browser.folder import ContentsView
from Products.CMFDefault.browser.tests.utils import clearVocabulary
from Products.CMFDefault.browser.tests.utils import setupVocabulary
from Products.CMFDefault.testing import FunctionalLayer


class FolderBrowserViewTests(unittest.TestCase):

    def setUp(self):
        """Setup a site"""
        # maybe there is a base class for this?
        self.site = site = DummySite('site')
        self.sm = getSiteManager()
        mtool = site._setObject('portal_membership', DummyTool())
        ptool = site._setObject('portal_properties', DummyTool())
        self.sm.registerUtility(ptool, IPropertiesTool)
        ttool = site._setObject('portal_types', DummyTool())
        utool = site._setObject('portal_url', DummyTool())
        folder = PortalFolder('test_folder')
        self.folder = site._setObject('test_folder', folder)
        self.uf = self.site._setObject('acl_users', DummyUserFolder())
        
    def _make_one(self, name="DummyItem"):
        content = DummyContent(name)
        content.portal_type = "Dummy Content"
        self.folder._setObject(name, content)

    def _make_batch(self):
        """Add enough objects to force pagination"""
        batch_size = ContentsView._BATCH_SIZE
        for i in range(batch_size + 2):
            content_id = "Dummy%s" % i
            self._make_one(content_id)

    def site_login(self):
        newSecurityManager(None, 
                    UnrestrictedUser('god', '', ['Manager'], ''))
    
    def test_view(self):
        view = ContentsView(self.folder, TestRequest())
        self.failUnless(IBrowserPublisher.providedBy(view))
        
    def test_up_info(self):
        view = ContentsView(self.folder, TestRequest())
        self.assertEquals({'url':u'', 'id':u'Root', 'icon':u''},
                            view.up_info())
        
    def test_list_batch_items(self):
        view = ContentsView(self.folder, TestRequest())
        self.assertEquals(view.listBatchItems(), [])
    
    def test_is_orderable(self):
        view = ContentsView(self.folder, TestRequest())
        self.failIf(view.is_orderable())
        
    def test_sort_can_be_changed(self):
        view = ContentsView(self.folder, TestRequest())
        self.failIf(view.can_sort_be_changed())
    
    def test_empty_has_subobjects(self):
        view = ContentsView(self.folder, TestRequest())
        self.failIf(view.has_subobjects())
        
    def test_has_subobjects(self):
        self._make_one()
        view = ContentsView(self.folder, TestRequest())
        self.failUnless(view.has_subobjects())
        
    def test_check_clipboard_data(self):
        view = ContentsView(self.folder, TestRequest())
        self.failIf(view.check_clipboard_data())
    
    def test_validate_items(self):
        """Cannot validate forms without widgets"""
        view = ContentsView(self.folder, TestRequest())
        self.assertRaises(AttributeError, 
                            view.validate_items, "", {'foo':'bar'})
                            
    def test_get_ids(self):
        view = ContentsView(self.folder, TestRequest())
        self.assertEquals(
                        view._get_ids({'foo':'bar'}),
                        [])
        self.assertEquals(
                        view._get_ids({'DummyItem1.select':True,
                                       'DummyItem2.select':False,
                                       'DummyItem3.select':True}),
                        ['DummyItem1', 'DummyItem3'])
        self.assertEquals(
                        view._get_ids({'delta':True,
                                       'delta':1}),
                        []
                        )


ftest_suite = ZopeTestCase.FunctionalDocFileSuite('folder.txt',
                        setUp=setupVocabulary,
                        tearDown=clearVocabulary,
                        )
                        
ftest_suite.layer = FunctionalLayer

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FolderBrowserViewTests))
    suite.addTest(unittest.TestSuite((ftest_suite,)))
    return suite
