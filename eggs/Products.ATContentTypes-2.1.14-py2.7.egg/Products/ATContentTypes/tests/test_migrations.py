from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase

from Products.ATContentTypes.config import TOOLNAME
from Products.ATContentTypes.migration.v1_2 import upgradeATCTTool
from Products.CMFCore.utils import getToolByName


class TestMigrations_v1_2(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        self.tool = getToolByName(self.portal, TOOLNAME)

    def testUpgradeATCTTool(self):
        self.assertEqual(self.tool.getProperty('album_batch_size'), 30)
        self.tool._setPropValue('album_batch_size', 99)
        self.tool._setPropValue('_version', '1.1.x (svn/testing)')
        upgradeATCTTool(self.portal)
        self.assertEqual(self.tool.getProperty('album_batch_size'), 99)

    def testUpgradeATCTToolTwice(self):
        self.assertEqual(self.tool.getProperty('album_batch_size'), 30)
        self.tool._setPropValue('album_batch_size', 99)
        self.tool._setPropValue('_version', '1.1.x (svn/testing)')
        upgradeATCTTool(self.portal)
        upgradeATCTTool(self.portal)
        self.assertEqual(self.tool.getProperty('album_batch_size'), 99)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v1_2))
    return suite
