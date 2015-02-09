# -*- coding: utf-8 -*-
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.app.testing import login

from zope.configuration import xmlconfig


class PlonePortletCollection(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.portlet.collection
        xmlconfig.file(
            'configure.zcml',
            plone.portlet.collection,
            context=configurationContext
        )

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.portlet.collection:default')
        portal.acl_users.userFolderAddUser('admin',
                                           'secret',
                                           ['Manager'],
                                           [])
        login(portal, 'admin')
        portal.portal_workflow.setDefaultChain("simple_publication_workflow")
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory(
            "Folder",
            id="robot-test-folder",
            title=u"Test Folder"
        )

PLONE_PORTLET_COLLECTION_FIXTURE = PlonePortletCollection()
PLONE_PORTLET_COLLECTION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_PORTLET_COLLECTION_FIXTURE,),
    name="PlonePortletCollection:Integration"
)
PLONE_PORTLET_COLLECTION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_PORTLET_COLLECTION_FIXTURE,),
    name="PlonePortletCollection:Functional"
)
