from plone.app.registry.browser import controlpanel
from experimental.safe_html_transform.interfaces import IExperimenatalSafe_Html_TransformSettings, _
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IFilterSchema
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.registry.interfaces import IRegistry
from zope.component import adapts
from zope.component import getUtility
from zope.interface import implements


class ISafe_Html_TransformSettingsEditForm(controlpanel.RegistryEditForm):
    schema = ISafe_Html_TransformSettings
    label = _(u"safe_html_transform settings")
    description = _(u"""""")

    def updateFields(self):
        super(ISafe_Html_TransformSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(ISafe_Html_TransformSettingsEditForm, self).updateWidgets()


class ISafe_Html_TransformSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = ISafe_Html_TransformSettingsEditForm


class FilterControlPanelAdapter(object):

    adapts(IPloneSiteRoot)
    implements(IFilterSchema)

    def __init__(self, context):
        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(IFilterSchema, prefix="plone")

    def get_nasty_tags(self):
        return self.settings.nasty_tags

    def set_nasty_tags(self, value):
        self.settings.nasty_tags = value

    def get_stripped_tags(self):
        return self.settings.stripped_tags

    def set_stripped_tags(self, value):
        self.settings.stripped_tags = value

    def get_custom_tags(self):
        return self.settings.custom_tags

    def set_custom_tags(self, value):
        self.settings.custom_tags = value

    def get_stripped_attributes(self):
        return self.settings.stripped_attributes

    def set_stripped_attributes(self, value):
        self.settings.stripped_attributes = value

    def get_style_whitelist(self):
        return self.settings.style_whitelist

    def set_style_whitelist(self, value):
        self.settings.style_whitelist = value

    def get_class_blacklist(self):
        return self.settings.class_blacklist

    def set_class_blacklist(self, value):
        self.settings.class_blacklist = value

    nasty_tags = property(get_nasty_tags, set_nasty_tags)
    stripped_tags = property(get_stripped_tags, set_stripped_tags)
    custom_tags = property(get_custom_tags, set_custom_tags)
    stripped_attributes = property(
        get_stripped_attributes,
        set_stripped_attributes
    )
    style_whitelist = property(get_style_whitelist, set_style_whitelist)
    class_blacklist = property(get_class_blacklist, set_class_blacklist)


#filtertagset = FormFieldsets(IFilterTagsSchema)
#filtertagset.id = 'filtertags'
#filtertagset.label = _(u'label_filtertags', default=u'Tags')
#
#filterattributes = FormFieldsets(IFilterAttributesSchema)
#filterattributes.id = 'filterattributes'
#filterattributes.label = _(u'label_filterattributes', default=u'Attributes')
#
#filtereditor = FormFieldsets(IFilterEditorSchema)
#filtereditor.id = 'filtereditor'
#filtereditor.label = _(u'filterstyles', default=u'Styles')
#
#tagattr_widget = CustomWidgetFactory(ObjectWidget, TagAttrPair)
#combination_widget = CustomWidgetFactory(ListSequenceWidget,
#                                         subwidget=tagattr_widget)

class FilterControlPanelForm(controlpanel.RegistryEditForm):

    id = "FilterControlPanel"
    label = _("HTML Filter settings")
    description = _("Plone filters HTML tags that are considered security "
                    "risks. Be aware of the implications before making "
                    "changes below. By default only tags defined in XHTML "
                    "are permitted. In particular, to allow 'embed' as a tag "
                    "you must both remove it from 'Nasty tags' and add it to "
                    "'Custom tags'. Although the form will update "
                    "immediately to show any changes you make, your changes "
                    "are not saved until you press the 'Save' button.")
    form_name = _("HTML Filter settings")
    schema = IFilterSchema
    schema_prefix = "plone"

#    form_fields = FormFieldsets(filtertagset, filterattributes, filtereditor)
#    form_fields['stripped_combinations'].custom_widget = combination_widget

    #form_fields = FormFieldsets(searchset)
    #form_fields['types_not_searched'].custom_widget = MCBThreeColumnWidget
    #form_fields['types_not_searched'].custom_widget.cssClass='label'

    def updateFields(self):
        super(FilterControlPanelForm, self).updateFields()


class FilterControlPanel(controlpanel.ControlPanelFormWrapper):
    form = FilterControlPanelForm
