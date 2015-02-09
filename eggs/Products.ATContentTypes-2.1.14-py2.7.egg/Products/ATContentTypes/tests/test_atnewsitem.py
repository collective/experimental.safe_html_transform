import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes import atapi
from Products.ATContentTypes.tests.utils import dcEdit

from Products.ATContentTypes.content.newsitem import ATNewsItem
from Products.ATContentTypes.tests.utils import NotRequiredTidyHTMLValidator
from Products.ATContentTypes.interfaces import ITextContent
from Products.ATContentTypes.interfaces import IImageContent
from Products.ATContentTypes.interfaces import IATNewsItem
from zope.interface.verify import verifyObject


tests = []

TEXT = "lorum ipsum"


def editATCT(obj):
    dcEdit(obj)
    obj.setText(TEXT)


class TestSiteATNewsItem(atcttestcase.ATCTTypeTestCase):

    klass = ATNewsItem
    portal_type = 'News Item'
    title = 'News Item'
    meta_type = 'ATNewsItem'

    def test_implementsTextContent(self):
        iface = ITextContent
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsImageContent(self):
        iface = IImageContent
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsATNewsItem(self):
        iface = IATNewsItem
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)

    def test_get_size(self):
        atct = self._ATCT
        editATCT(atct)
        self.assertEqual(atct.get_size(), len(TEXT))

tests.append(TestSiteATNewsItem)


class TestATNewsItemFields(atcttestcase.ATCTFieldTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATNewsItem)

    def test_textField(self):
        dummy = self._dummy
        field = dummy.getField('text')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getText',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setText',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission == ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'text', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AnnotationStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AnnotationStorage(migrate=True),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == NotRequiredTidyHTMLValidator,
                        'Value is %s' % repr(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.RichWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

        self.assertTrue(field.primary == 1, 'Value is %s' % field.primary)
        self.assertTrue(field.default_content_type is None,
                        'Value is %s' % field.default_content_type)
        self.assertTrue(field.default_output_type == 'text/x-html-safe',
                        'Value is %s' % field.default_output_type)
        self.assertTrue('text/html' in field.getAllowedContentTypes(dummy))

tests.append(TestATNewsItemFields)


class TestATNewsItemFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'News Item'
    views = ('newsitem_view', )

tests.append(TestATNewsItemFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
