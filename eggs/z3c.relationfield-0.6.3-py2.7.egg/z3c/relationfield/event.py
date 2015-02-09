# -*- coding: UTF-8 -*-
from z3c.relationfield.interfaces import IHasIncomingRelations
from z3c.relationfield.interfaces import IHasOutgoingRelations
from z3c.relationfield.interfaces import IRelation
from z3c.relationfield.interfaces import IRelationList
from z3c.relationfield.interfaces import IRelationValue
from z3c.relationfield.interfaces import ITemporaryRelationValue
from zc.relation.interfaces import ICatalog
from zope import component
from zope.intid.interfaces import IIntIds
from zope.event import notify
from zope.interface import providedBy
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getFields


def addRelations(obj, event):
    """Register relations.

    Any relation object on the object will be added.
    """
    for name, relation in _relations(obj):
        _setRelation(obj, name, relation)


# zope.app.intid dispatches a normal event, so we need to check that
# the object has relations.  This adds a little overhead to every
# intid registration, which would not be needed if an object event
# were dispatched in zope.app.intid.
def addRelationsEventOnly(event):
    obj = event.object
    if not IHasOutgoingRelations.providedBy(obj):
        return
    addRelations(obj, event)


def removeRelations(obj, event):
    """Remove relations.

    Any relation object on the object will be removed from the catalog.
    """
    catalog = component.queryUtility(ICatalog)
    if catalog is None:
        return

    for name, relation in _relations(obj):
        if relation is not None:
            try:
                catalog.unindex(relation)
            except KeyError:
                # The relation value has already been unindexed.
                pass


def updateRelations(obj, event):
    """Re-register relations, after they have been changed.
    """
    catalog = component.queryUtility(ICatalog)
    intids = component.queryUtility(IIntIds)

    if catalog is None or intids is None:
        return

    # check that the object has an intid, otherwise there's nothing to be done
    try:
        obj_id = intids.getId(obj)
    except KeyError:
        # The object has not been added to the ZODB yet
        return

    # remove previous relations coming from id (now have been overwritten)
    # have to activate query here with list() before unindexing them so we don't
    # get errors involving buckets changing size
    rels = list(catalog.findRelations({'from_id': obj_id}))
    for rel in rels:
        catalog.unindex(rel)

    # add new relations
    addRelations(obj, event)


def breakRelations(event):
    """Break relations on any object pointing to us.

    That is, store the object path on the broken relation.
    """
    obj = event.object
    if not IHasIncomingRelations.providedBy(obj):
        return
    catalog = component.queryUtility(ICatalog)
    intids = component.queryUtility(IIntIds)
    if catalog is None or intids is None:
        return

    # find all relations that point to us
    try:
        obj_id = intids.getId(obj)
    except KeyError:
        # our intid was unregistered already
        return
    rels = list(catalog.findRelations({'to_id': intids.getId(obj)}))
    for rel in rels:
        rel.broken(rel.to_path)
        # we also need to update the relations for these objects
        notify(ObjectModifiedEvent(rel.from_object))


def realize_relations(obj):
    """Given an object, convert any temporary relations on it to real ones.
    """
    for name, index, relation in _potential_relations(obj):
        if ITemporaryRelationValue.providedBy(relation):
            if index is None:
                # relation
                setattr(obj, name, relation.convert())
            else:
                # relation list
                getattr(obj, name)[index] = relation.convert()


def _setRelation(obj, name, value):
    """Set a relation on an object.

    Sets up various essential attributes on the relation.
    """
    # if the Relation is None, we're done
    if value is None:
        return
    # make sure relation has a __parent__ so we can make an intid for it
    value.__parent__ = obj
    # also set from_object to parent object
    value.from_object = obj
    # and the attribute to the attribute name
    value.from_attribute = name
    # now we can create an intid for the relation
    intids = component.getUtility(IIntIds)
    id = intids.register(value)
    # and index the relation with the catalog
    catalog = component.getUtility(ICatalog)
    catalog.index_doc(id, value)


def _relations(obj):
    """Given an object, return tuples of name, relation value.

    Only real relations are returned, not temporary relations.
    """
    for name, index, relation in _potential_relations(obj):
        if IRelationValue.providedBy(relation):
            yield name, relation


def _potential_relations(obj):
    """Given an object return tuples of name, index, relation value.

    Returns both IRelationValue attributes as well as ITemporaryRelationValue
    attributes.

    If this is a IRelationList attribute, index will contain the index
    in the list. If it's a IRelation attribute, index will be None.
    """
    for iface in providedBy(obj).flattened():
        for name, field in getFields(iface).items():
            if IRelation.providedBy(field):
                try:
                    relation = getattr(obj, name)
                except AttributeError:
                    # can't find this relation on the object
                    continue
                yield name, None, relation
            if IRelationList.providedBy(field):
                try:
                    l = getattr(obj, name)
                except AttributeError:
                    # can't find the relation list on this object
                    continue
                if l is not None:
                    for i, relation in enumerate(l):
                        yield name, i, relation
