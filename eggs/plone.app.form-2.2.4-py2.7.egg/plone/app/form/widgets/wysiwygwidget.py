from zope.formlib.textwidgets import TextWidget

from Acquisition import aq_parent
from Products.CMFCore.interfaces import ISiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from zope.component.hooks import getSite


class WYSIWYGWidget(TextWidget):
    """ A widget using Plone's wysiwyg_support.
    """

    template = ViewPageTemplateFile('wysiwygwidget.pt')

    def __init__(self, field, request):
        super(TextWidget, self).__init__(field, request)

    def __call__(self):
        value = self._getFormValue()
        if value is None or value == self.context.missing_value:
            value = ''

        # Evil acquisition majik to find the site root. This is made tricky
        # by the fact that the widget doesn't have a direct path to its
        # context (you can go self.context.context, but this may be an
        # adapter on the context, not the context itself.). We can find
        # the root using getUtility(ISiteRoot), but this isn't wrapped
        # in the request container. We can use getSite(), but there may be
        # other sites in-between, not at least the KSS site-in-a-view. Sigh.

        site = getSite()
        while site is not None and not ISiteRoot.providedBy(site):
            site = aq_parent(site)
        
        return self.template(form_context=site,
                             value=value)