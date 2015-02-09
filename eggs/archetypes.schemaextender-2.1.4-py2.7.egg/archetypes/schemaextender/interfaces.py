from zope.interface import Interface
from zope.configuration.fields import GlobalInterface


class IExtensible(Interface):
    """Marker interface applied to extensible content types
    """


class IExtensionField(Interface):
    """Extension field"""

    def getAccessor(instance):
        """Return the accessor method for getting data out of this field."""

    def getEditAccessor(instance):
        """Return the accessor method for getting raw data out of this field
        e.g.: for editing.
        """

    def getMutator(instance):
        """Return the mutator method used for changing the value of this field.
        """

    def getIndexAccessor(instance):
        """Return the index accessor, i.e. the getter for an indexable value.
        """


class ITranslatableExtensionField(IExtensionField):
    """Extension field for ITranslatable"""

    def getTranslationMutator(instance):
        """Return a mutator for translatable values"""

    def isLanguageIndependent(instance):
        """Get the language independed flag for i18n content."""


class ISchemaExtender(Interface):
    """Interface for adapters that extend the schema"""

    def __init__(context):
        """Constructor. Takes the instance whose schema we are frobbing."""

    def getFields():
        """Return a list of fields to be added to the schema."""


class IOrderableSchemaExtender(ISchemaExtender):
    """An orderable version of the schema extender"""

    def getOrder(original):
        """Return the optionally reordered fields.

        'original' is a dictionary where the keys are the names of
        schemata and the values are lists of field names, in order.

        The method should return a new such dictionary with re-ordered
        lists.

        It is recommended to use an OrderedDict (available as
        Products.Archetypes.utils.OrderedDict) to guarantee proper ordering
        of schemata.
        """


class IBrowserLayerAwareExtender(Interface):
    """An plone browserlayer aware schemaextender.

    Extenders with this interface are used only in context of the given
    browserlayer.
    """

    layer = GlobalInterface()


class ISchemaModifier(Interface):
    """Interface for adapters that modify the existing schema.

    Before you're allowed to use this method, you must take the Oath
    of the Schema Modifier. Repeat after us:

      "I <name>, hereby do solemnly swear, to refrain, under any
       circumstances, from using this adapter for Evil. I will not
       delete fields, change field types or do other breakable and evil
       things. Promise."

    Okay, then we can all move on.
    """

    def __init__(context):
        """Constructor. Takes the instance whose schema we are frobbing."""

    def fiddle(schema):
        """Fiddle the schema.

        This is a copy of the class' schema, with any ISchemaExtender-provided
        fields added. The schema may be modified in-place: there is no
        need to return a value.

        In general, it will be a bad idea to delete or materially change
        fields, since other components may depend on these ones.

        If you change any fields, then you are responsible for making a copy of
        them first and place the copy in the schema.
        """
