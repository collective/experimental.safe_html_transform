from Products.CMFPlone import PloneMessageFactory as _
from plone.app.registry.browser import controlpanel
from Products.CMFCore.interfaces import ISiteRoot
from plone.app.layout.navigation.interfaces import INavigationRoot
from zope.interface import Interface
from zope import schema
from zope.interface import implements


class IPloneSiteRoot(ISiteRoot, INavigationRoot):
    """
    Marker interface for the object which serves as the root of a
    Plone site.
    """


class ITagAttrPair(Interface):
    tags = schema.TextLine(title=u"tags")
    attributes = schema.TextLine(title=u"attributes")


class TagAttrPair:
    implements(ITagAttrPair)

    def __init__(self, tags='', attributes=''):
        self.tags = tags
        self.attributes = attributes


class IFilterTagsSchema(Interface):
    nasty_tags = schema.List(
        title=_(u'Nasty tags'),
        description=_(u"These tags, and their content are completely blocked "
                      "when a page is saved or rendered."),
        default=[u'applet', u'embed', u'object', u'script'],
        value_type=schema.TextLine(),
        required=False
    )

    stripped_tags = schema.List(
        title=_(u'Stripped tags'),
        description=_(u"These tags are stripped when saving or rendering, "
                      "but any content is preserved."),
        default=[u'font', ],
        value_type=schema.TextLine(),
        required=False
    )

    custom_tags = schema.List(
        title=_(u'Custom tags'),
        description=_(u"Add tag names here for tags which are not part of "
                      "XHTML but which should be permitted."),
        default=[],
        value_type=schema.TextLine(),
        required=False
    )


class IFilterAttributesSchema(Interface):
    stripped_attributes = schema.List(
        title=_(u'Stripped attributes'),
        description=_(u"These attributes are stripped from any tag when "
                      "saving."),
        default=(u'dir lang valign halign border frame rules cellspacing '
                 'cellpadding bgcolor').split(),
        value_type=schema.TextLine(),
        required=False)


class IFilterEditorSchema(Interface):

    style_whitelist = schema.List(
        title=_(u'Permitted styles'),
        description=_(u'These CSS styles are allowed in style attributes.'),
        default=u'text-align list-style-type float'.split(),
        value_type=schema.TextLine(),
        required=False)

    class_blacklist = schema.List(
        title=_(u'Filtered classes'),
        description=_(u'These class names are not allowed in class '
                      'attributes.'),
        default=[],
        value_type=schema.TextLine(),
        required=False)


class IFilterSchema(IFilterTagsSchema, IFilterAttributesSchema,
                    IFilterEditorSchema):
    """Combined schema for the adapter lookup.
    """


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

    def updateFields(self):
        super(FilterControlPanelForm, self).updateFields()


class FilterControlPanel(controlpanel.ControlPanelFormWrapper):
    form = FilterControlPanelForm
