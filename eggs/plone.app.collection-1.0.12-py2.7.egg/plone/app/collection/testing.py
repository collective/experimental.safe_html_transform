# -*- coding: utf-8 -*-
import doctest

from zope.configuration import xmlconfig

from plone.testing import z2

from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing.layers import FunctionalTesting
from plone.app.testing.layers import IntegrationTesting
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE


class PloneAppCollectionLayer(PloneSandboxLayer):

    def setUpZope(self, app, configurationContext):
        import plone.app.collection
        xmlconfig.file(
            'configure.zcml',
            plone.app.collection,
            context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.collection:default')
        portal.acl_users.userFolderAddUser('admin',
                                           'secret',
                                           ['Manager'],
                                           [])
        login(portal, 'admin')
        portal.portal_workflow.setDefaultChain("simple_publication_workflow")
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory(
            "Folder",
            id="test-folder",
            title=u"Test Folder"
        )


PLONEAPPCOLLECTION_FIXTURE = PloneAppCollectionLayer()

PLONEAPPCOLLECTION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONEAPPCOLLECTION_FIXTURE,),
    name="PloneAppCollectionLayer:Integration")

PLONEAPPCOLLECTION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONEAPPCOLLECTION_FIXTURE,),
    name="PloneAppCollectionLayer:Functional")

PLONEAPPCOLLECTION_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(PLONEAPPCOLLECTION_FIXTURE, z2.ZSERVER_FIXTURE),
    name="PloneAppCollectionLayer:Acceptance")

PLONEAPPCOLLECTION_ROBOT_TESTING = FunctionalTesting(
    bases=(PLONEAPPCOLLECTION_FIXTURE,
           REMOTE_LIBRARY_BUNDLE_FIXTURE,
           z2.ZSERVER_FIXTURE),
    name="PloneAppCollectionLayer:Robot")

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
