import logging
import traceback
from smtplib import SMTPException

from plone.contentrules.rule.interfaces import IRuleElementData, IExecutable
from plone.stringinterp.interfaces import IStringInterpolator
from zope.component import adapts
from zope.component.interfaces import ComponentLookupError
from zope.formlib import form
from zope.interface import Interface, implements
from zope import schema
from zope.globalrequest import getRequest

from Acquisition import aq_inner
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.MailHost.MailHost import MailHostError
from Products.statusmessages.interfaces import IStatusMessage

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


logger = logging.getLogger("plone.contentrules")


class IMailAction(Interface):
    """Definition of the configuration available for a mail action
    """
    subject = schema.TextLine(title=_(u"Subject"),
                              description=_(u"Subject of the message"),
                              required=True)
    source = schema.TextLine(title=_(u"Email source"),
                             description=_("The email address that sends the "
                                           "email. If no email is provided here, "
                                           "it will use the portal from address."),
                             required=False)
    recipients = schema.TextLine(title=_(u"Email recipients"),
                                description=_("The email where you want to "
                                              "send this message. To send it to "
                                              "different email addresses, "
                                              "just separate them with ,"),
                                required=True)
    exclude_actor = schema.Bool(title=_(u"Exclude actor from recipients"),
                                description=_("Do not send the email to the user "
                                              "that did the action."))
    message = schema.Text(title=_(u"Message"),
                          description=_(u"The message that you want to mail."),
                          required=True)


class MailAction(SimpleItem):
    """
    The implementation of the action defined before
    """
    implements(IMailAction, IRuleElementData)

    subject = u''
    source = u''
    recipients = u''
    message = u''
    exclude_actor = False

    element = 'plone.actions.Mail'

    @property
    def summary(self):
        return _(u"Email report to ${recipients}",
                 mapping=dict(recipients=self.recipients))


class MailActionExecutor(object):
    """The executor for this action.
    """
    implements(IExecutable)
    adapts(Interface, IMailAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        mailhost = getToolByName(aq_inner(self.context), "MailHost")
        if not mailhost:
            raise ComponentLookupError, "You must have a Mailhost utility to \
execute this action"

        urltool = getToolByName(aq_inner(self.context), "portal_url")
        portal = urltool.getPortalObject()
        email_charset = portal.getProperty('email_charset')

        obj = self.event.object

        interpolator = IStringInterpolator(obj)

        source = self.element.source
        if source:
            source = interpolator(source).strip()

        if not source:
            # no source provided, looking for the site wide from email
            # address
            from_address = portal.getProperty('email_from_address')
            if not from_address:
                # the mail can't be sent. Try to inform the user
                request = getRequest()
                if request:
                    messages = IStatusMessage(request)
                    msg = _(u"Error sending email from content rule. You must "
                            "provide a source address for mail "
                            "actions or enter an email in the portal properties")
                    messages.add(msg, type=u"error")
                return False

            from_name = portal.getProperty('email_from_name').strip('"')
            source = '"%s" <%s>' % (from_name, from_address)

        recip_string = interpolator(self.element.recipients)
        if recip_string: # check recipient is not None or empty string
            recipients = set([str(mail.strip()) for mail in recip_string.split(',') \
                              if mail.strip()])
        else:
            recipients = set()

        if self.element.exclude_actor:
            mtool = getToolByName(aq_inner(self.context), "portal_membership")
            actor_email = mtool.getAuthenticatedMember().getProperty('email', '')
            if actor_email in recipients:
                recipients.remove(actor_email)

        # prepend interpolated message with \n to avoid interpretation
        # of first line as header
        message = "\n%s" % interpolator(self.element.message)

        subject = interpolator(self.element.subject)

        for email_recipient in recipients:
            try:
                # XXX: We're using "immediate=True" because otherwise we won't
                # be able to catch SMTPException as the smtp connection is made
                # as part of the transaction apparatus.
                # AlecM thinks this wouldn't be a problem if mail queuing was
                # always on -- but it isn't. (stevem)
                # so we test if queue is not on to set immediate
                mailhost.send(message, email_recipient, source,
                              subject=subject, charset=email_charset,
                              immediate=not mailhost.smtp_queue)
            except (MailHostError, SMTPException):
                logger.error(
                    """mailing error: Attempt to send mail in content rule failed.\n%s""" %
                    traceback.format_exc())

        return True


class MailAddForm(AddForm):
    """
    An add form for the mail action
    """
    form_fields = form.FormFields(IMailAction)
    label = _(u"Add Mail Action")
    description = _(u"A mail action can mail different recipient.")
    form_name = _(u"Configure element")

    # custom template will allow us to add help text
    template = ViewPageTemplateFile('templates/mail.pt')

    def create(self, data):
        a = MailAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class MailEditForm(EditForm):
    """
    An edit form for the mail action
    """
    form_fields = form.FormFields(IMailAction)
    label = _(u"Edit Mail Action")
    description = _(u"A mail action can mail different recipient.")
    form_name = _(u"Configure element")

    # custom template will allow us to add help text
    template = ViewPageTemplateFile('templates/mail.pt')
