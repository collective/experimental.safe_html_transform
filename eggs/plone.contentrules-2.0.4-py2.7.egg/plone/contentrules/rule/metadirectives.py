from zope.interface import Interface

from zope import schema
from zope.configuration import fields as configuration_fields

class IRuleElementDirective(Interface):
    """Directive which registers a new rule element.

    The actual directives will use IRuleActionDirective or IRuleConditionDirective
    """

    name = schema.TextLine(
        title=u"Name",
        description=u"A unique name for the element",
        required=True)

    title = schema.TextLine(
        title=u"Title",
        description=u"A user-friendly title for the element",
        required=True)

    description = schema.Text(
        title=u"Description",
        description=u"A helpful description of the element",
        required=False)

    for_ = configuration_fields.GlobalInterface(
        title = u"Available for",
        description = u"The interface this element is available for",
        required = False)

    event = configuration_fields.GlobalInterface(
        title = u"Event",
        description = u"The event this element is available for",
        required = False)

    addview = schema.TextLine(
        title = u"Add view",
        description = u"Name of the add view",
        required = True)

    editview = schema.TextLine(
        title = u"Edit view",
        description = u"Name of the edit view",
        required = False)

    schema = configuration_fields.GlobalInterface(
        title = u"Schema",
        description = u"The schema interface for configuring the element",
        required = False)

    factory = configuration_fields.GlobalObject(
        title = u"Factory",
        description = u"A callable which can create the element",
        required = False)

class IRuleActionDirective(IRuleElementDirective):
    """An element directive describing what is logically an action element.
    """

class IRuleConditionDirective(IRuleElementDirective):
    """An element directive describing what is logically a condition element.
    """
