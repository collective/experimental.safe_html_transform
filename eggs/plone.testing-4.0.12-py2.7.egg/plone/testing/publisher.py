"""Helpers for working with common Zope publisher operations
"""

from plone.testing import Layer
from plone.testing import zca, security

class PublisherDirectives(Layer):
    """Enables the use of the ZCML directives from ``zope.app.publisher``
    (most of the ``browser`` namespace, excluding viewlets), and
    ``zope.security`` (the ``permission`` directive).

    Extends ``zca.ZCML_DIRECTIVES`` and uses its ``configurationContext``
    resource.
    """

    defaultBases = (zca.ZCML_DIRECTIVES, security.CHECKERS)

    def setUp(self):
        from zope.configuration import xmlconfig

        # Stack a new configuration context
        self['configurationContext'] = context = zca.stackConfigurationContext(self.get('configurationContext'))

        import zope.security
        xmlconfig.file('meta.zcml', zope.security, context=context)

        # XXX: In Zope 2.13, this has split into zope.publisher,
        # zope.browserresource, zope.browsermenu and zope.browserpage
        import zope.app.publisher
        xmlconfig.file('meta.zcml', zope.app.publisher, context=context)

    def tearDown(self):
        # Zap the stacked configuration context
        del self['configurationContext']

PUBLISHER_DIRECTIVES = PublisherDirectives()
