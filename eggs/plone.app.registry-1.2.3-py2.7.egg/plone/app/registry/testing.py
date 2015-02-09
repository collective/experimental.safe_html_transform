from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting

from zope.configuration import xmlconfig


class PloneAppRegistry(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import plone.app.registry
        xmlconfig.file('configure.zcml', plone.app.registry, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.registry:default')


PLONE_APP_REGISTRY_FIXTURE = PloneAppRegistry()

PLONE_APP_REGISTRY_INTEGRATION_TESTING = \
    IntegrationTesting(bases=(PLONE_APP_REGISTRY_FIXTURE, ), name="plone.app.registry:Integration")
