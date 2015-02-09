from doctest import DocTestSuite
import unittest


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('Products.CMFQuickInstallerTool.QuickInstallerTool'),
        DocTestSuite('Products.CMFQuickInstallerTool.InstalledProduct')))
