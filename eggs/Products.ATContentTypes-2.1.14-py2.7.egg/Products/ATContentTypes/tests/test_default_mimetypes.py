# test initialisation and setup

from Products.ATContentTypes.tests.atcttestcase import ATCTSiteTestCase
from unittest import TestSuite, makeSuite


class TestDefaultMimeTypes(ATCTSiteTestCase):

    def test_ATDocumentDefaultType(self):
        self.loginAsPortalOwner()
        # we create a new document:
        self.portal.invokeFactory('Document', id='testdoc', title='TestDocument')
        obj = self.portal.testdoc
        # its text field should have the site wide default 'text/html'
        textfield = obj.getField('text')
        self.assertEqual(textfield.getContentType(obj), 'text/html')
        # but not the description field:
        descriptionfield = obj.getField('description')
        self.assertEqual(descriptionfield.getContentType(obj), 'text/plain')

        # then we change the sitewide default:
        from Products.Archetypes.mimetype_utils import setDefaultContentType
        setDefaultContentType(self.portal, "text/x-web-markdown")
        self.assertEqual(textfield.getContentType(obj), 'text/html')
        # this should only affect new objects:
        self.assertFalse(textfield.getContentType(obj) == 'text/x-web-markdown')
        self.portal.invokeFactory('Document', id='testdoc2', title='TestDocument with new default')
        second_object = self.portal.testdoc2
        second_field = second_object.getField('text')
        self.assertTrue(second_field.getContentType(second_object) == 'text/x-web-markdown')


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestDefaultMimeTypes))
    return suite
