# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.dexterity.fti import DexterityFTI
from zope.configuration import xmlconfig


class PloneAppUUID(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import plone.app.uuid
        xmlconfig.file('configure.zcml', plone.app.uuid, context=configurationContext)

    def setUpPloneSite(self, portal):
        types_tool = getToolByName(portal, "portal_types")
        # This test should work for both Plone 4.3 (with ATContentTypes) and
        # Plone 5.x (without any types). Therefore we can not make any
        # assumptions about an existing Document type.
        if 'Document' not in types_tool.objectIds():
            fti = DexterityFTI('Document')
            types_tool._setObject('Document', fti)


PLONE_APP_UUID_FIXTURE = PloneAppUUID()
PLONE_APP_UUID_INTEGRATION_TESTING = \
    IntegrationTesting(bases=(PLONE_APP_UUID_FIXTURE,), name="plone.app.uuid:Integration")
PLONE_APP_UUID_FUNCTIONAL_TESTING = \
    FunctionalTesting(bases=(PLONE_APP_UUID_FIXTURE,), name="plone.app.uuid:Functional")
