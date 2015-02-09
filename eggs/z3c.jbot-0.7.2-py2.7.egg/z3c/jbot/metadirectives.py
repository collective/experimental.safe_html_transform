from zope.interface import Interface
from zope.configuration import fields
from zope.configuration.fields import GlobalObject

class ITemplateOverridesDirective(Interface):
    """Directive which registers a directory with template overrides."""

    directory = fields.Path(
        title=u"Path to directory",
        required=True)

    layer = GlobalObject(
        title=u"The layer the overrides should be enabled for",
        description=u"By default overrides are used for all layers.",
        required=False
        )

