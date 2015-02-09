import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase
from DateTime import DateTime
import Missing

tests = []


class TestFormatCatalogMetadata(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTSiteTestCase.afterSetUp(self)
        self.script = self.portal.formatCatalogMetadata

    def testFormatDate(self):
        date = '2005-11-02 13:52:25'
        toLocalizedTime = self.portal.toLocalizedTime
        self.assertEqual(self.script(date),
                         toLocalizedTime(date, long_format=True))
        self.assertEqual(self.script(DateTime(date)),
                         toLocalizedTime(date, long_format=True))

    def testFormatDict(self):
        self.assertEqual(self.script({'a': 1, 'b': 2}), 'a: 1, b: 2')

    def testFormatList(self):
        self.assertEqual(self.script(('a', 'b', 1, 2, 3, 4)),
                         'a, b, 1, 2, 3, 4')
        self.assertEqual(self.script(['a', 'b', 1, 2, 3, 4]),
                         'a, b, 1, 2, 3, 4')
        # this also needs to be able to handle unicode that won't encode to ascii
        ustr = 'i\xc3\xadacute'.decode('utf8')
        self.assertEqual(self.script(['a', 'b', ustr]),
                         'a, b, i\xc3\xadacute'.decode('utf8'))

    def testFormatString(self):
        self.assertEqual(self.script('fkj dsh ekjhsdf kjer'), 'fkj dsh ekjhsdf kjer')

    def testFormatTruncates(self):
        self.portal.portal_properties.site_properties.manage_changeProperties(
                            search_results_description_length=12, ellipsis='???')
        self.assertEqual(self.script('fkj dsh ekjhsdf kjer'), 'fkj dsh ekjh???')

    def testFormatStrange(self):
        self.assertEqual(self.script(None), '')
        self.assertEqual(self.script(Missing.Value()), '')

    def testUnicodeValue(self):
        """ Make sure non-ascii encodable unicode is acceptable """

        ustr = 'i\xc3\xadacute'.decode('utf8')
        self.assertEqual(self.script(ustr), ustr)

tests.append(TestFormatCatalogMetadata)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
