# -*- coding: utf-8 -*-
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
        self.browser.open(self.portal_url + '/@@filter-controlpanel')
        self.assertTrue(
            self.browser.url.endswith('filter-controlpanel'))

    def test_save_button(self):
        self.browser.open(self.portal_url + '/@@filter-controlpanel')
        self.browser.getControl(name="form.buttons.save").click()
        self.assertTrue(
            self.browser.url.endswith('filter-controlpanel'))

    def test_status_msg_after_save(self):
        self.browser.open(self.portal_url + '/@@filter-controlpanel')
        self.browser.getControl(name="form.buttons.save").click()
        self.assertTrue(
            'Changes saved.' in self.browser.contents)

    def test_cancel_button(self):
        self.browser.open(self.portal_url + '/@@filter-controlpanel')
        self.browser.getControl(name="form.buttons.cancel").click()
        self.assertTrue(
            self.browser.url.endswith('plone_control_panel'))

    def test_status_msg_after_cancel(self):
        self.browser.open(self.portal_url + '/@@filter-controlpanel')
        self.browser.getControl(name="form.buttons.cancel").click()
        self.assertTrue(
            'Changes canceled.' in self.browser.contents)

    def test_add_new_link(self):
        self.browser.open('http://nohost/plone/portal_factory/Document/document.2015-08-14.9025882105/edit')
        # self.browser.getLink('Add new').click()
        self.assertTrue(
            'Add Page' in self.browser.contents)

    def test_add_new_content(self):
        self.browser.open('http://nohost/plone/portal_factory/Document/document.2015-08-18.4050665269/edit')
        # self.browser.getLink('Add new').click()
        self.assertTrue(
            'Body Text' in self.browser.contents)
        self.browser.getControl('Body Text').value = \
            '<p>Testing that<script> tag and its contents get stripped</script> works.</p>'
        self.browser.getControl('Title').value = 'LOL'
        self.browser.getControl('Save').click()
        self.assertTrue(
            'Changes saved.' in self.browser.contents)
        self.assertTrue(
            'LOL' in self.browser.contents)
        self.assertTrue(
            '<p>Testing that<script> tag and its contents get stripped</script> works.</p>' in self.browser.contents
        )
