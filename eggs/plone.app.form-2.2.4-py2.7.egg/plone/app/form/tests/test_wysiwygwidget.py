from Products.PloneTestCase import PloneTestCase as ptc
from Products.CMFCore.utils import getToolByName

from zope.publisher.browser import TestRequest
from zope.site.hooks import getSite

from plone.app.form.widgets.wysiwygwidget import WYSIWYGWidget

ptc.setupPloneSite()

BODY = """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"
      xmlns:tal="http://xml.zope.org/namespaces/tal"
      xmlns:metal="http://xml.zope.org/namespaces/metal"
      xmlns:i18n="http://xml.zope.org/namespaces/i18n"
      i18n:domain="plone">

<div metal:define-macro="wysiwygEditorBox">
  <div>Cool Editor Box</div>
  <textarea name="description"
            rows="25"
            tal:content="inputvalue"
            tal:attributes="name inputname;
                            id inputname;"></textarea>
</div>

</html>
"""


class WYSIWYGWidgetTestCase(ptc.PloneTestCase):
    """Base class used for test cases
    """

    def test_right_macro(self):
        # fixes #8016
        class MyField:
            __name__ = 'the field'
            required = True
            default = u'the value'
            missing_value = None
            title = ""
            description = ""

        # Let's add a custom editor using our own widget html:
        from zope.pagetemplate.pagetemplatefile import PageTemplate
        template = PageTemplate()
        template.pt_edit(BODY, 'text/html')
        site = getSite()
        site.portal_skins.custom.cool_editor_wysiwyg_support = template

        # The wysiwyg widget depends on the used editor.
        # Let's change it to `cool_editor`.
        pm = getToolByName(self.portal, 'portal_membership')
        member = pm.getAuthenticatedMember()
        member.setMemberProperties({'wysiwyg_editor': 'cool_editor'})

        w = WYSIWYGWidget(MyField(), TestRequest())
        # The test is partially that this call does not give an error:
        html = w()
        # This is true for standard Plone as well:
        self.assertTrue(
            '<textarea name="field.the field" rows="25" id="field.the field">'
            'the value</textarea>' in html)
        # Only our cool editor has this:
        self.assertTrue('Cool Editor Box' in html)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(WYSIWYGWidgetTestCase))
    return suite
