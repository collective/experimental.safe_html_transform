from z3c.relationfield.interfaces import IRelation
from z3c.relationfield.interfaces import IRelationChoice
from z3c.relationfield.interfaces import IRelationList
from zope.interface import implements
from zope.schema import Field, List, Choice


class Relation(Field):
    implements(IRelation)


class RelationList(List):
    implements(IRelationList)

    def __init__(self, value_type=None, unique=False, **kw):
        if value_type is None:
            value_type = Relation()
        super(RelationList, self).__init__(
            value_type=value_type,
            unique=unique,
            **kw
        )


class RelationChoice(Choice):
    implements(IRelationChoice)
