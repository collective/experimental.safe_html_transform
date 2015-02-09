from datetime import date

from zope.globalrequest import setRequest

from plone.namedfile import NamedFile
from Products.CMFDiffTool.interfaces import IDifference

from Products.PloneTestCase import PloneTestCase

from Products.CMFDiffTool import testing
from Products.CMFDiffTool.dexteritydiff import DexterityCompoundDiff
from Products.CMFDiffTool.dexteritydiff import EXCLUDED_FIELDS


class DexterityDiffTestCase(PloneTestCase.FunctionalTestCase):

    layer = testing.package_layer

    def afterSetUp(self):
        setRequest(self.portal.REQUEST)
        self.loginAsPortalOwner()

    def test_should_diff(self):
        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj1',
            title=u'Object 1',
            description=u'Desc 1',
            text=u'Text 1'
        )
        obj1 = self.portal['obj1']

        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj2',
            title=u'Object 2',
            text=u'Text 2'
        )
        obj2 = self.portal['obj2']

        diffs = DexterityCompoundDiff(obj1, obj2, 'any')
        for d in diffs:
            self.assertTrue(IDifference.providedBy(d))
            self.assertFalse(d.field in EXCLUDED_FIELDS)
            if d.field in ['title', 'description', 'text']:
                self.assertFalse(
                    d.same, 'Field %s should be different.' % d.field)
            else:
                self.assertTrue(d.same, 'Field %s should be equal.' % d.field)

    def test_should_provide_inline_diff_for_date_field(self):
        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj1',
            date=date(2001, 1, 1),
        )
        obj1 = self.portal['obj1']

        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj2',
            date=date(2001, 1, 2),
        )
        obj2 = self.portal['obj2']

        diffs = DexterityCompoundDiff(obj1, obj2, 'any')
        for d in diffs:
            if d.field == 'date':
                self.assertTrue(d.inline_diff())

    def test_should_provide_inline_diff_for_file_list_field(self):
        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj1',
            files=None,
        )
        obj1 = self.portal['obj1']

        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj2',
            files=[NamedFile(data='data', filename=u'a.txt')],
        )
        obj2 = self.portal['obj2']

        diffs = DexterityCompoundDiff(obj1, obj2, 'any')
        for d in diffs:
            if d.field == 'files':
                inline_diff = d.inline_diff()
                self.assertTrue(inline_diff)
                self.assertTrue(obj2.files[0].filename in inline_diff)
