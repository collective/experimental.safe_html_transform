from Products.CMFCore.utils import getToolByName

from Products.PloneTestCase import PloneTestCase

from Products.CMFDiffTool.dexteritydiff import DexterityCompoundDiff
from Products.CMFDiffTool import testing


class InstallTestCase(PloneTestCase.FunctionalTestCase):

    layer = testing.package_layer

    def test_compound_diff_type_should_be_registered(self):
        diff_tool = getToolByName(self.portal, 'portal_diff')
        self.assertTrue(
            DexterityCompoundDiff.meta_type in diff_tool.listDiffTypes())
        self.assertTrue(
            diff_tool.getDiffType(DexterityCompoundDiff.meta_type))
