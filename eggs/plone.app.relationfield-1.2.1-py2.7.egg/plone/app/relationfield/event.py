from zope.schema import getFields
from plone.behavior.interfaces import IBehaviorAssignable
from z3c.relationfield.event import _setRelation
from z3c.relationfield.interfaces import (
    IRelation,
    IRelationList,
)


def extract_relations(obj):
    assignable = IBehaviorAssignable(obj, None)
    if assignable is None:
        return
    for behavior in assignable.enumerateBehaviors():
        if behavior.marker != behavior.interface:
            for name, field in getFields(behavior.interface).items():
                if IRelation.providedBy(field):
                    try:
                        relation = getattr(behavior.interface(obj), name)
                    except AttributeError:
                        continue
                    yield behavior.interface, name, relation
                if IRelationList.providedBy(field):
                    try:
                        l = getattr(behavior.interface(obj), name)
                    except AttributeError:
                        continue
                    if l is not None:
                        for relation in l:
                            yield behavior.interface, name, relation


def update_behavior_relations(obj, event):
    """Re-register relations in behaviors
    """
    for behavior_interface, name, relation in extract_relations(obj):
        _setRelation(obj, name, relation)
