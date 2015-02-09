from zope.interface import implements, Interface, Attribute
from zope.interface.common.sequence import IReadSequence

class IField(Interface):
    """A Field: a behavioral object associated to a context and a
    value"""


try:
    from Products.Archetypes.interfaces import IATField
    class IATField(IField, IATField):
        """ at specific field interface """
except ImportError:
    pass


class IFieldValue(Interface):
    """ a value derived from the context. could be anything """

class IFieldValueSetter(Interface):
    """ stores a value derived from the context. """

class IFieldEvent(Interface):
    """ something has happened involving a field """
    value = Attribute("the value to render forth")
    instance = Attribute("the context object")
    field = Attribute("the field object")
    kwargs = Attribute("AT compatibility cruft")

    def __init__(field_, instance, **kwargs):
        """everything needed to make AT rendering go"""

class IFieldRenderEvent(IFieldEvent):
    """ an container to fetch a value for a field """

class IFieldStorageEvent(IFieldEvent):
    """ an container to store a value for a field """

class ITxtFilter(Interface):
    """Abstract Base for filters.

    Filters happen during object access (rendering for example) and
    include the context the object is being run in.
    """
    name = Attribute('name for this filter')

    def __init__(field, context, event):
        """to initialize.
        """

    def __call__():
        """execute filter. must be a callable.
        """

class ITxtFilterList(IReadSequence):
    """list of txtfilter names to apply"""

## events and exceptions ##

class FieldEvent(object):
    implements(IFieldEvent)
    value=None
    def __init__(self, field_, instance, **kwargs):
        self.field = field_
        self.instance = instance
        self.kwargs = kwargs

class FieldStorageEvent(FieldEvent):
    implements(IFieldStorageEvent)
    def __init__(self, field_, instance, value, **kwargs):
        super(FieldStorageEvent, self).__init__(field_, instance, **kwargs)
        self.value = value

class FieldRenderEvent(FieldEvent):
    implements(IFieldRenderEvent)

class EndFiltrationException(Exception):
    """raise to stop continuation of txtfiltering"""
