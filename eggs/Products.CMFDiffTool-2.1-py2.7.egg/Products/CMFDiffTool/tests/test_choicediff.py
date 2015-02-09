from Products.CMFDiffTool.choicediff import ChoiceDiff
from Products.CMFDiffTool.choicediff import title_or_value
from Products.CMFDiffTool.interfaces import IDifference

from Products.PloneTestCase import PloneTestCase
from Products.CMFDiffTool import testing


class ChoiceDiffTestCase(PloneTestCase.FunctionalTestCase):

    layer = testing.package_layer

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj1',
        )
        self.portal.invokeFactory(
            testing.TEST_CONTENT_TYPE_ID,
            'obj2',
        )

        self.obj1 = self.portal['obj1']
        self.obj2 = self.portal['obj2']

    def test_should_diff_choice_field(self):
        self._test_diff_choice(testing.VOCABULARY_TUPLES[0][0],
                               testing.VOCABULARY_TUPLES[0][0], True)
        self._test_diff_choice(testing.VOCABULARY_TUPLES[0][0],
                               testing.VOCABULARY_TUPLES[1][0], False)
        self._test_diff_choice(testing.VOCABULARY_TUPLES[1][0],
                               testing.VOCABULARY_TUPLES[0][0], False)
        self._test_diff_choice(testing.VOCABULARY_TUPLES[1][0],
                               testing.VOCABULARY_TUPLES[1][0], True)

        self._test_diff_choice(testing.VOCABULARY_TUPLES[0][0], None, False)
        self._test_diff_choice(testing.VOCABULARY_TUPLES[1][0], None, False)
        self._test_diff_choice(None, testing.VOCABULARY_TUPLES[0][0], False)
        self._test_diff_choice(None, testing.VOCABULARY_TUPLES[1][0], False)
        self._test_diff_choice(None, None, True)

    def _test_diff_choice(self, value1, value2, same):
        self.obj1.choice = value1
        self.obj2.choice = value2
        diff = ChoiceDiff(self.obj1, self.obj2, 'choice')
        self.assertTrue(IDifference.providedBy(diff))
        self.assertEqual(diff.same, same)

        inline_diff = diff.inline_diff()
        if same:
            self.assertFalse(inline_diff)
        else:
            if value1 is not None:
                self.assertTrue(
                    title_or_value(testing.VOCABULARY, value1) in inline_diff)
            if value2 is not None:
                self.assertTrue(
                    title_or_value(testing.VOCABULARY, value2) in inline_diff)
