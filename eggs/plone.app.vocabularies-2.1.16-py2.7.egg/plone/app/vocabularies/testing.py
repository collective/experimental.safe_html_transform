from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer


class PAVocabulariesLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import plone.app.vocabularies
        self.loadZCML(
            package=plone.app.vocabularies,
            context=configurationContext
        )

PAVocabularies_FIXTURE = PAVocabulariesLayer()
PAVocabularies_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PAVocabularies_FIXTURE,),
    name="PAVocabularies:Integration")
