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

    def test_post_product_uninstall(self):
        """Test if Portal Transform is installed or not after uninstalling experimental.safe_html_transform"""
        self.installer.uninstallProducts(['experimental.safe_html_transform'])
        self.assertTrue(self.installer.isProductInstalled('Products.PortalTransform'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that IExperimentalSafeHtmlTransformLayer is registered."""
        from experimental.safe_html_transform.interfaces import IExperimentalSafeHtmlTransformLayer
        from plone.browserlayer import utils
        self.assertIn(IExperimentalSafeHtmlTransformLayer, utils.registered_layers())

    def test_portal_title(self):
        """Test the title of the package is experimental_safe_html_transform"""
        portal = self.layer['portal']
        self.assertTrue('experimental.safe_html_transform', portal.getProperty('title'))

    def test_portal_description(self):
        """Test the description of the package"""
        portal = self.layer['portal']
        self.assertTrue("Installs the experimental.safe_html_transform add-on.", portal.getProperty('description'))
