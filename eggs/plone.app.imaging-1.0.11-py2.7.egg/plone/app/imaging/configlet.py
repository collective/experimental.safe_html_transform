from plone.app.controlpanel.form import ControlPanelForm
from plone.app.imaging.interfaces import IImagingSchema, _
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFDefault.formlib.schema import ProxyFieldProperty
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapts, getUtility
from zope.formlib.form import FormFields
from zope.interface import implements


class ImagingControlPanelAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(IImagingSchema)

    def __init__(self, context):
        super(ImagingControlPanelAdapter, self).__init__(context)
        self.context = getUtility(IPropertiesTool).imaging_properties

    allowed_sizes = ProxyFieldProperty(IImagingSchema['allowed_sizes'])
    quality = ProxyFieldProperty(IImagingSchema['quality'])


class ImagingControlPanel(ControlPanelForm):

    form_fields = FormFields(IImagingSchema)

    label = _('Image handling settings')
    description = _('Settings to configure image handling in Plone.')
    form_name = _('Imaging scaling')
