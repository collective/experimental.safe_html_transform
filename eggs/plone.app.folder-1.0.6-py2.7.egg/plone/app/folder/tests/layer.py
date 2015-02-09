from zope.component import provideAdapter

from Testing.ZopeTestCase import app, close, installPackage
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.layer import PloneSite
from transaction import commit

from plone.folder.partial import PartialOrdering

# BBB Zope 2.12
try:
    from Zope2.App.zcml import load_config
    load_config # pyflakes
    from OFS import metaconfigure
    metaconfigure # pyflakes
except ImportError:
    from Products.Five.zcml import load_config
    from Products.Five import fiveconfigure as metaconfigure


class IntegrationLayer(PloneSite):
    """ layer for integration tests using the folder replacement type """

    @classmethod
    def setUp(cls):
        root = app()
        portal = root.plone
        # load zcml & install the package
        metaconfigure.debug_mode = True
        from plone.app.folder import tests
        load_config('testing.zcml', tests)
        metaconfigure.debug_mode = False
        installPackage('plone.app.folder', quiet=True)
        # import replacement profile
        profile = 'profile-plone.app.folder:default'
        tool = getToolByName(portal, 'portal_setup')
        tool.runAllImportStepsFromProfile(profile, purge_old=False)
        # make sure it's loaded...
        types = getToolByName(portal, 'portal_types')
        assert types.getTypeInfo('Folder').product == 'plone.app.folder'
        # and commit the changes
        commit()
        close(root)

    @classmethod
    def tearDown(cls):
        pass


class PartialOrderingIntegrationLayer(IntegrationLayer):
    """ layer for integration tests using the partial ordering adapter """

    @classmethod
    def setUp(cls):
        provideAdapter(PartialOrdering)

    @classmethod
    def tearDown(cls):
        pass
