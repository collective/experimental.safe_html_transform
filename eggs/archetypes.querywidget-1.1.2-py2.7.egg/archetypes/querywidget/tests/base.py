import unittest2 as unittest

from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing.layers import IntegrationTesting
from plone.testing import z2
from zope.component import getGlobalSiteManager
from zope.configuration import xmlconfig
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class StringVocab(object):
    def __call__(self, context):
        return SimpleVocabulary([
            SimpleTerm(value='b', title=u'Second'),
            SimpleTerm(value='c', title=u'Third'),
            SimpleTerm(value='a', title=u'First'),
        ])


class IntVocab(object):
    def __call__(self, context):
        return SimpleVocabulary([
            SimpleTerm(value=2, title=u'Second'),
            SimpleTerm(value=3, title=u'Third'),
            SimpleTerm(value=1, title=u'First'),
        ])
INT_VOCAB = IntVocab()
STR_VOCAB = StringVocab()


class ArchetypesQueryWidgetLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def registerVocabularies(self):
        gsm = getGlobalSiteManager()
        gsm.registerUtility(STR_VOCAB, IVocabularyFactory, u'archetypes.querywidget.string_vocab')
        gsm.registerUtility(INT_VOCAB, IVocabularyFactory, u'archetypes.querywidget.int_vocab')

    def setUpZope(self, app, configurationContext):
        import archetypes.querywidget
        xmlconfig.file('configure.zcml', archetypes.querywidget,
                       context=configurationContext)

        import plone.app.collection
        xmlconfig.file('configure.zcml', plone.app.collection,
                       context=configurationContext)
        z2.installProduct(app, 'plone.app.collection')
        z2.installProduct(app, 'Products.ATContentTypes')

    def setUpPloneSite(self, portal):
        self.registerVocabularies()
        if 'Document' not in portal.portal_types:
            applyProfile(portal, 'Products.ATContentTypes:default')
        applyProfile(portal, 'plone.app.collection:default')
        applyProfile(portal, 'archetypes.querywidget:test_fixture')
        portal.acl_users.userFolderAddUser('admin',
                                           'secret',
                                           ['Manager'],
                                           [])
        login(portal, 'admin')

        # enable workflow for browser tests
        workflow = portal.portal_workflow
        workflow.setDefaultChain('simple_publication_workflow')

        # add a page, so we can test with it
        portal.invokeFactory("Document",
                             "document",
                             title="Document Test Page")
        # and add a collection so we can test the widget
        portal.invokeFactory("Collection",
                             "collection",
                             title="Test Collection")

        workflow.doActionFor(portal.document, "publish")
        workflow.doActionFor(portal.collection, "publish")


QUERYWIDGET_FIXTURE = ArchetypesQueryWidgetLayer()

QUERYWIDGET_INTEGRATION_TESTING = IntegrationTesting(
    bases=(QUERYWIDGET_FIXTURE,),
    name="ArchetypesQueryWidget:Integration")


class ArchetypesQueryWidgetTestCase(unittest.TestCase):
    layer = QUERYWIDGET_INTEGRATION_TESTING
