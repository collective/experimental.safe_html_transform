from Products.ATContentTypes.interface import IATDocument
from Products.Archetypes.public import StringField
from Products.Archetypes.public import StringWidget
from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import ISchemaExtender
from zope.component import adapts
from zope.interface import implements


class MyStringField(ExtensionField, StringField):
    """A trivial field."""


class PageExtender(object):
    adapts(IATDocument)  # XXX Might not work on Plone 3.
    implements(ISchemaExtender)

    fields = [
        MyStringField(
            "extensive_text",
            default="default text",
            widget=StringWidget(
                label="This page has extensive text")),
            ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields
