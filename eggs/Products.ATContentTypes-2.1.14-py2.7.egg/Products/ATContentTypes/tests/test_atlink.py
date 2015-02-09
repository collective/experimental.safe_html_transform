import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes import atapi

from Products.ATContentTypes.content.link import ATLink
from Products.ATContentTypes.interfaces import IATLink
from zope.interface.verify import verifyObject

URL = 'http://www.example.org/'


def editATCT(obj):
    obj.setTitle('Test Title')
    obj.setDescription('Test description')
    obj.setRemoteUrl(URL)

tests = []


class TestSiteATLink(atcttestcase.ATCTTypeTestCase):

    klass = ATLink
    portal_type = 'Link'
    title = 'Link'
    meta_type = 'ATLink'

    def test_implementsATLink(self):
        iface = IATLink
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def testLink(self):
        obj = self._ATCT

        url = 'http://www.example.org/'
        obj.setRemoteUrl(url)
        self.assertEqual(obj.getRemoteUrl(), url)

        url = 'false:url'
        obj.setRemoteUrl(url)
        self.assertEqual(obj.getRemoteUrl(), url)

    def testLinkSanitizesOutput(self):
        obj = self._ATCT

        url = 'javascript:alert("test")'
        obj.setRemoteUrl(url)
        self.assertEqual(obj.getRemoteUrl(),
                             'javascript:alert%28%22test%22%29')
        # Keep question marks and ampersands intact, please.
        url = 'http://something.sane/f.php?p1=value&p2=value'
        obj.setRemoteUrl(url)
        self.assertEqual(obj.getRemoteUrl(),
                             'http://something.sane/f.php?p1=value&p2=value')
        # already quoted values should also remain intact
        url = 'http://something.sane/except with spaces in it'
        expected = 'http://something.sane/except%20with%20spaces%20in%20it'
        obj.setRemoteUrl(url)
        self.assertEqual(obj.getRemoteUrl(), expected)
        obj.setRemoteUrl(obj.getRemoteUrl())
        self.assertEqual(obj.getRemoteUrl(), expected)

    def test_edit(self):
        new = self._ATCT
        editATCT(new)

    def test_get_size(self):
        atct = self._ATCT
        editATCT(atct)
        self.assertEqual(atct.get_size(), len(URL))

tests.append(TestSiteATLink)


class TestATLinkFields(atcttestcase.ATCTFieldTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATLink)

    def test_remoteUrlField(self):
        dummy = self._dummy
        field = dummy.getField('remoteUrl')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 1, 'Value is %s' % field.required)
        self.assertTrue(field.default == 'http://', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getRemoteUrl',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setRemoteUrl',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission == ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'string', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AttributeStorage(),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == (),
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.StringWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))
        self.assertTrue(field.primary == 1, 'Value is %s' % field.primary)

tests.append(TestATLinkFields)


class TestATLinkFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'Link'
    views = ('link_view', )

tests.append(TestATLinkFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
