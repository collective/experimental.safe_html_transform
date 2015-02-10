# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
# from z3c.form import interfaces
from zope import schema
from zope.interface import Interface
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
_ = MessageFactory('experimental.safe_html_transform')


class IExperimentalSafeHtmlTransformLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


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

#    stripped_combinations = schema.List(
#        title=_(u'Stripped combinations'),
#        description=_(u"These attributes are stripped from those tags when "
#                      "saving."),
#        default=[],
#        #default=u'dir lang valign halign border frame rules cellspacing
#        # cellpadding bgcolor'.split()
#        value_type=schema.Object(ITagAttrPair, title=u"combination"),
#        required=False)


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
