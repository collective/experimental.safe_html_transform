import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase
from Products.validation.interfaces.IValidator import IValidationChain
from Products.ATContentTypes.content.schemata import ATContentTypeSchema

tests = []


class TestBugs(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTSiteTestCase.afterSetUp(self)
        self.wf = self.portal.portal_workflow

    def test_wfmapping(self):
        default = ('simple_publication_workflow',)

        mapping = {
            'Document': default,
            'Event': default,
            'File': (),
            'Folder': default,
            'Image': (),
            'Link': default,
            'News Item': default,
            'Topic': default,
            }

        for pt, wf in mapping.items():
            pwf = self.wf.getChainFor(pt)
            self.assertEqual(pwf, wf, (pt, pwf, wf))

    def test_striphtmlbug(self):
        # Test for Plone tracker #4944
        self.folder.invokeFactory('Document', 'document')
        d = getattr(self.folder, 'document')
        d.setTitle("HTML end tags start with </ and end with >")
        self.assertEqual(d.Title(), "HTML end tags start with </ and end with >")

    def test_validation_layer_from_id_field_from_base_schema_was_initialized(self):
        field = ATContentTypeSchema['id']
        self.assertTrue(IValidationChain.providedBy(field.validators))

tests.append(TestBugs)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
