from zope.interface import implements
from zope.component import getMultiAdapter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from plone.app.openid import PloneMessageFactory as _


class ILoginPortlet(IPortletDataProvider):
    """A portlet which can render an OpenID login form.
    """


class Assignment(base.Assignment):
    implements(ILoginPortlet)

    title = _(u'OpenID login')


class Renderer(base.Renderer):

    def __init__(self, context, request, view, manager, data):
        base.Renderer.__init__(self, context, request, view, manager, data)

        self.portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
        self.pas_info = getMultiAdapter((context, request), name=u'pas_info')

    @property
    def available(self):
        if not self.portal_state.anonymous():
            return False
        if not self.pas_info.hasOpenIDExtractor():
            return False
        page = self.request.get('URL', '').split('/')[-1]
        return page not in ('login_form', '@@register')

    def login_form(self):
        return '%s/login_form' % self.portal_state.portal_url()


    render = ViewPageTemplateFile('login.pt')


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
