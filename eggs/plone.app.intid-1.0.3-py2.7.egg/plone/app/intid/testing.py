# -*- coding: utf-8 -*-
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting


class IntidSetupFixture(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # pylint: disable=W0613
        import plone.app.intid
        self.loadZCML(package=plone.app.intid)


SETUP_TESTING = IntegrationTesting(
    bases=(IntidSetupFixture(),), name="IntidSetupFixture:Setup")
