import logging

from zope.component import adapts
from zope.component.interfaces import IObjectEvent
from zope.formlib import form
from zope.interface import implements, Interface
from zope import schema

from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


logger = logging.getLogger("plone.contentrules.logger")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s -  %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class ILoggerAction(Interface):
    """Interface for the configurable aspects of a logger action.

    This is also used to create add and edit forms, below.
    """

    targetLogger = schema.ASCIILine(title=_(u'Logger name'),
                                    default='Plone')

    loggingLevel = schema.Int(title=_(u'Logging level'),
                              default=20) # INFO

    message = schema.TextLine(title=_(u"Message"),
                              description=_('help_contentrules_logger_message',
                                            default=u"&e = the triggering event, &c = the context, &u = the user"),
                              default=_('text_contentrules_logger_message',
                                        default=u"Caught &e at &c by &u"))


class LoggerAction(SimpleItem):
    """The actual persistent implementation of the logger action element.

    Note that we must mix in Explicit to keep Zope 2 security happy.
    """
    implements(ILoggerAction, IRuleElementData)

    targetLogger = ''
    loggingLevel = ''
    message = ''

    element = 'plone.actions.Logger'

    @property
    def summary(self):
        return _(u"Log message ${message}", mapping=dict(message=self.message))


class LoggerActionExecutor(object):
    """The executor for this action.

    This is registered as an adapter in configure.zcml
    """
    implements(IExecutable)
    adapts(Interface, ILoggerAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def processedMessage(self):
        processedMessage = self.element.message
        if "&e" in processedMessage:
            processedMessage = processedMessage.replace("&e", "%s.%s" % (
                    self.event.__class__.__module__, self.event.__class__.__name__))

        if "&c" in processedMessage and IObjectEvent.providedBy(self.event):
            processedMessage = processedMessage.replace("&c", repr(self.event.object))

        if "&u" in processedMessage:
            mtool = getToolByName(self.context, 'portal_membership')
            member = mtool.getAuthenticatedMember().getUserName()
            processedMessage = processedMessage.replace("&u", member)

        return processedMessage

    def __call__(self):
        logger = logging.getLogger(self.element.targetLogger)
        logger.log(self.element.loggingLevel, self.processedMessage())
        return True


class LoggerAddForm(AddForm):
    """An add form for logger rule actions.
    """
    form_fields = form.FormFields(ILoggerAction)
    label = _(u"Add Logger Action")
    description = _(u"A logger action can output a message to the system log.")
    form_name = _(u"Configure element")

    def create(self, data):
        a = LoggerAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class LoggerEditForm(EditForm):
    """An edit form for logger rule actions.

    Formlib does all the magic here.
    """
    form_fields = form.FormFields(ILoggerAction)
    label = _(u"Edit Logger Action")
    description = _(u"A logger action can output a message to the system log.")
    form_name = _(u"Configure element")
