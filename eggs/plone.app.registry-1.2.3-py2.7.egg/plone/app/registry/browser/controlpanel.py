from zope.component import getUtility

from plone.registry.interfaces import IRegistry

from z3c.form import form, button

from plone.z3cform import layout
from plone.autoform.form import AutoExtensibleForm

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('plone')


class RegistryEditForm(AutoExtensibleForm, form.EditForm):
    """Edit a records proxy based on an interface.

    To use this, you should use the <records /> element in a registry.xml
    GS import step to register records for a particular interface. Then
    subclass this form and set the 'schema' class variable to point to
    the same interface. You can use plone.autoform form hints to affect the
    rendering of the form, or override the update() method as appropriate.

    To get the standard control panel layout, use ControlPanelFormWrapper as
    the form wrapper, e.g.

        from plone.app.registry.browser.form import RegistryEditForm
        from plone.app.registry.browser.form import ControlPanelFormWrapper
        from my.package.interfaces import IMySettings
        form plone.z3cform import layout

        class MyForm(RegistryEditForm):
            schema = IMySettings

        MyFormView = layout.wrap_form(MyForm, ControlPanelFormWrapper)

    Then register MyFormView as a browser view.
    """

    control_panel_view = "plone_control_panel"
    schema_prefix = None

    def getContent(self):
        return getUtility(IRegistry).forInterface(
            self.schema,
            prefix=self.schema_prefix)

    def updateActions(self):
        super(RegistryEditForm, self).updateActions()
        self.actions['save'].addClass("context")
        self.actions['cancel'].addClass("standalone")

    @button.buttonAndHandler(_(u"Save"), name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(
            _(u"Changes saved."),
            "info")
        self.request.response.redirect(self.request.getURL())

    @button.buttonAndHandler(_(u"Cancel"), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _(u"Changes canceled."),
            "info")
        self.request.response.redirect("%s/%s" % (
            self.context.absolute_url(),
            self.control_panel_view))


class ControlPanelFormWrapper(layout.FormWrapper):
    """Use this form as the plone.z3cform layout wrapper to get the control
    panel layout.
    """

    index = ViewPageTemplateFile('controlpanel_layout.pt')
