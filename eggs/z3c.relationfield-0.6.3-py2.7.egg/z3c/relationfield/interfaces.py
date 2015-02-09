from zope.interface import Interface, Attribute
from zope.schema.interfaces import IField, IList

class IHasOutgoingRelations(Interface):
    """Marker interface indicating that the object has outgoing relations.

    Provide this interface on your own objects with outgoing relations
    to make sure that the relations get added and removed from the
    catalog when appropriate.
    """

class IHasIncomingRelations(Interface):
    """Marker interface indicating the the object has incoming relations.

    Provide this interface on your own objects with incoming
    relations. This will make sure that broken relations to that
    object are tracked properly.
    """
    
class IHasRelations(IHasIncomingRelations, IHasOutgoingRelations):
    """Marker interface indicating that the object has relations of any kind.

    Provide this interface if the object can have both outgoing as
    well as incoming relations.
    """

class IRelation(IField):
    """Simple one to one relations.
    """

class IRelationChoice(IRelation):
    """A one to one relation where a choice of target objects is available.
    """

class IRelationList(IList):
    """A one to many relation.
    """

class IRelationValue(Interface):
    """A relation between the parent object and another one.

    This should be stored as the value in the object when the schema uses the
    Relation field.
    """
    from_object = Attribute("The object this relation is pointing from.")

    from_id = Attribute("Id of the object this relation is pointing from.")
    
    from_path = Attribute("The path of the from object.")

    from_interfaces = Attribute("The interfaces of the from object.")

    from_interfaces_flattened = Attribute(
        "Interfaces of the from object, flattened. "
        "This includes all base interfaces.")
    
    from_attribute = Attribute("The name of the attribute of the from object.")
    
    to_object = Attribute("The object this relation is pointing to. "
                          "This value is None if the relation is broken.")

    to_id = Attribute("Id of the object this relation is pointing to. "
                      "This value is None if the relation is broken.")

    to_path = Attribute("The path of the object this relation is pointing to. "
                        "If the relation is broken, this value will still "
                        "point to the last path the relation pointed to.")

    to_interfaces = Attribute("The interfaces of the to-object.")

    to_interfaces_flattened = Attribute(
        "The interfaces of the to object, flattened. "
        "This includes all base interfaces.")

    def broken(to_path):
        """Set this relation as broken.

        to_path - the (non-nonexistent) path that the relation pointed to.

        The relation will be broken. If you provide
        IHasIncomingRelations on objects that have incoming relations,
        relations will be automatically broken when you remove an
        object.
        """

    def isBroken():
        """Return True if this is a broken relation.
        """

class ITemporaryRelationValue(Interface):
    """A temporary relation.

    When importing relations from XML, we cannot resolve them into
    true RelationValue objects yet, as it may be that the object that is
    being related to has not yet been loaded. Instead we create
    a TemporaryRelationValue object that can be converted into a real one
    after the import has been concluded.
    """
    def convert():
        """Convert temporary relation into a real one.

        Returns real relation object
        """
