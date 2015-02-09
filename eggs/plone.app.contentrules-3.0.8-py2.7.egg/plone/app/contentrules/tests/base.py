"""Base class for integration tests, based on ZopeTestCase and PloneTestCase.

Note that importing this module has various side-effects: it registers a set of
products with Zope, and it sets up a sandbox Plone site with the appropriate
products installed.
"""

# Import PloneTestCase - this registers more products with Zope as a side effect
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from zope.component import getMultiAdapter

# Set up a Plone site - note that the portlets branch of CMFPlone applies
# a portlets profile.
setupPloneSite()


class ContentRulesTestCase(PloneTestCase):
    """Base class for integration tests for plone.app.contentrules. This may
    provide specific set-up and tear-down operations, or provide convenience
    methods.
    """

    def addAuthToRequest(self):
        portal = self.portal
        request = portal.REQUEST
        authenticator = getMultiAdapter((portal, request), name=u"authenticator")
        auth = authenticator.authenticator().split('value="')[1].rstrip('"/>')
        request.form['_authenticator'] = auth

class ContentRulesFunctionalTestCase(FunctionalTestCase):
    """Base class for functional integration tests for plone.app.portlets.
    This may provide specific set-up and tear-down operations, or provide
    convenience methods.
    """
