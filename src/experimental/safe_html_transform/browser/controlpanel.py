from plone.app.registry.browser import controlpanel
 
from experimental.safe_html_transform.interfaces import IExperimenatalSafe_Html_TransformSettings, _
 
 
class IExperimenatalSafe_Html_TransformSettingsEditForm(controlpanel.RegistryEditForm):
 
    schema = IExperimenatalSafe_Html_TransformSettings
    label = _(u"experimentalsafe_html_transform settings")
    description = _(u"""""")
 
    def updateFields(self):
        super(IExperimenatalSafe_Html_TransformSettingsEditForm, self).updateFields()
 
 
    def updateWidgets(self):
        super(IExperimenatalSafe_Html_TransformSettingsEditForm, self).updateWidgets()
 
class IExperimenatalSafe_Html_TransformSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = IExperimenatalSafe_Html_TransformSettingsEditForm