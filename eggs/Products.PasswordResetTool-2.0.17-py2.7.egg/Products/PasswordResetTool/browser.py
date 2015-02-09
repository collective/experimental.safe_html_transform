from Acquisition import aq_inner
from zope.interface import implements
from zope.component import getMultiAdapter
from Products.Five import BrowserView
from plone.memoize import view
from Products.CMFPlone.utils import safe_unicode
from zope.i18n import translate

from Products.PasswordResetTool.interfaces import IPasswordResetToolView
from Products.PasswordResetTool import passwordresetMessageFactory as _
from email.Header import Header

class PasswordResetToolView(BrowserView):
    implements(IPasswordResetToolView)

    @view.memoize_contextless
    def tools(self):
        """ returns tools view. Available items are all portal_xxxxx
            For example: catalog, membership, url
            http://dev.plone.org/plone/browser/plone.app.layout/trunk/plone/app/layout/globals/tools.py
        """
        return getMultiAdapter((self.context, self.request), name=u"plone_tools")

    @view.memoize_contextless
    def portal_state(self):
        """ returns
            http://dev.plone.org/plone/browser/plone.app.layout/trunk/plone/app/layout/globals/portal.py
        """
        return getMultiAdapter((self.context, self.request), name=u"plone_portal_state")

    def encode_mail_header(self, text):
        """ Encodes text into correctly encoded email header """
        return Header(safe_unicode(text), 'utf-8')

    def encoded_mail_sender(self):
        """ returns encoded version of Portal name <portal_email> """
        portal = self.portal_state().portal()
        from_ = portal.getProperty('email_from_name')
        mail  = portal.getProperty('email_from_address')
        return '"%s" <%s>' % (self.encode_mail_header(from_), mail)

    def registered_notify_subject(self):
        portal = self.portal_state().portal()
        portal_name = portal.Title()
        return translate(_(u"mailtemplate_user_account_info",
                           default=u"User Account Information for ${portal_name}",
                           mapping={'portal_name':safe_unicode(portal_name)}),
                           context=self.request)

    def mail_password_subject(self):
        portal = self.portal_state().portal()
        portal_name = portal.Title()
        return translate(_(u"mailtemplate_subject_resetpasswordrequest",
                           default=u"Password reset request"),
                           context=self.request)
