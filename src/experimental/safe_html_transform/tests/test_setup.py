# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""
from experimental.safe_html_transform.testing import EXPERIMENTAL_SAFE_HTML_TRANSFORM_INTEGRATION_TESTING  # noqa
from plone import api

import unittest2 as unittest


class TestInstall(unittest.TestCase):
    """Test installation of experimental.safe_html_transform into Plone."""

    layer = EXPERIMENTAL_SAFE_HTML_TRANSFORM_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if experimental.safe_html_transform is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('experimental.safe_html_transform'))

    def test_uninstall(self):
        """Test if experimental.safe_html_transform is cleanly uninstalled."""
        self.installer.uninstallProducts(['experimental.safe_html_transform'])
        self.assertFalse(self.installer.isProductInstalled('experimental.safe_html_transform'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that IExperimentalSafeHtmlTransformLayer is registered."""
        from experimental.safe_html_transform.interfaces import IExperimentalSafeHtmlTransformLayer
        from plone.browserlayer import utils
        self.assertIn(IExperimentalSafeHtmlTransformLayer, utils.registered_layers())
