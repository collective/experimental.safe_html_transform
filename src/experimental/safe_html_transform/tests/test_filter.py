from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from experimental.safe_html_transform.testing import \
    EXPERIMENTAL_SAFE_HTML_TRANSFORM_FUNCTIONAL_TESTING
from plone.testing.z2 import Browser
import unittest2 as unittest


class DocumentFunctionalTest(unittest.TestCase):

    layer = EXPERIMENTAL_SAFE_HTML_TRANSFORM_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_url_end(self):
        self.browser.open(self.portal_url + '/@@safe_html_transform-settings')
        self.assertTrue(
            self.browser.url.endswith('safe_html_transform-settings'))
