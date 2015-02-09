import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase
from Products.ATContentTypes.config import TOOLNAME
from Products.ATContentTypes.interfaces import IATCTTool
from zope.interface.verify import verifyObject
from Products.CMFCore.utils import getToolByName

tests = []


class TestTool(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        self.tool = getToolByName(self.portal, TOOLNAME)

    def test_interface(self):
        t = self.tool
        self.assertTrue(IATCTTool.providedBy(t))
        self.assertTrue(verifyObject(IATCTTool, t))

    def test_names(self):
        t = self.tool
        self.assertEqual(t.meta_type, 'ATCT Tool')
        self.assertEqual(t.getId(), TOOLNAME)
        self.assertEqual(t.title, 'Collection and image scales settings')

tests.append(TestTool)


class TestATCTToolFunctional(atctftestcase.IntegrationTestCase):

    zmi_tabs = ('manage_imageScales', 'manage_overview', )

    def setupTestObject(self):
        self.obj_id = TOOLNAME
        self.obj = getToolByName(self.portal, TOOLNAME)
        self.obj_url = self.obj.absolute_url()
        self.obj_path = '/%s' % self.obj.absolute_url(1)

    def test_zmi_tabs(self):
        for view in self.zmi_tabs:
            response = self.publish('%s/%s' % (self.obj_path, view), self.owner_auth)
            self.assertEqual(response.getStatus(), 200,
                "%s: %s" % (view, response.getStatus()))  # OK

tests.append(TestATCTToolFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
