import unittest2 as unittest

from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from zope.configuration import xmlconfig


class ContentListingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        import plone.app.layout
        import plone.app.contentlisting
        xmlconfig.file('configure.zcml',
                       plone.app.layout, context=configurationContext)
        xmlconfig.file('configure.zcml',
                       plone.app.contentlisting, context=configurationContext)


CONTENTLISTING_FIXTURE = ContentListingLayer()
CONTENTLISTING_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CONTENTLISTING_FIXTURE, ), name="ContentListing:Integration")
CONTENTLISTING_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CONTENTLISTING_FIXTURE, ), name="ContentListing:Functional")


class ContentlistingTestCase(unittest.TestCase):
    layer = CONTENTLISTING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setDefaultChain('simple_publication_workflow')

        self.portal.invokeFactory('Folder', 'test-folder')
        self.portal.invokeFactory('Document', 'front-page')
        self.portal.invokeFactory('Folder', 'news')
        wftool.doActionFor(self.portal.news, 'publish')
        self.portal.news.invokeFactory('News Item', 'news1')
        setRoles(self.portal, TEST_USER_ID, ['Member'])

        self.folder = self.portal['test-folder']


class ContentlistingFunctionalTestCase(ContentlistingTestCase):
    layer = CONTENTLISTING_FUNCTIONAL_TESTING
