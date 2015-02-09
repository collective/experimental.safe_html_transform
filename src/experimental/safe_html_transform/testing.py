# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from zope.configuration import xmlconfig

import experimental.safe_html_transform


class ExperimentalSafeHtmlTransformLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        xmlconfig.file(
            'configure.zcml',
            experimental.safe_html_transform,
            context=configurationContext
        )

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'experimental.safe_html_transform:default')


EXPERIMENTAL_SAFE_HTML_TRANSFORM_FIXTURE = ExperimentalSafeHtmlTransformLayer()


EXPERIMENTAL_SAFE_HTML_TRANSFORM_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EXPERIMENTAL_SAFE_HTML_TRANSFORM_FIXTURE,),
    name='ExperimentalSafeHtmlTransformLayer:IntegrationTesting'
)


EXPERIMENTAL_SAFE_HTML_TRANSFORM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EXPERIMENTAL_SAFE_HTML_TRANSFORM_FIXTURE,),
    name='ExperimentalSafeHtmlTransformLayer:FunctionalTesting'
)


EXPERIMENTAL_SAFE_HTML_TRANSFORM_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EXPERIMENTAL_SAFE_HTML_TRANSFORM_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='ExperimentalSafeHtmlTransformLayer:AcceptanceTesting'
)
