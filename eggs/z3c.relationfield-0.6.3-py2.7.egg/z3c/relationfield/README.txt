z3c.relationfield
*****************

Introduction
============

This package implements a new schema field Relation, and the
RelationValue objects that store actual relations. It can index these
relations using the ``zc.relation`` infractructure, and using these
indexes can efficiently answer questions about the relations.

The package `z3c.relationfieldui`_ in addition provides a widget to
edit and display Relation fields.

.. _`z3c.relationfieldui`: http://pypi.python.org/pypi/z3c.relationfieldui

Setup
=====

``z3c.relationfield.Relation`` is a schema field that can be used to
express relations. Let's define a schema IItem that uses a relation
field::

  >>> from z3c.relationfield import Relation
  >>> from zope.interface import Interface
  >>> class IItem(Interface):
  ...   rel = Relation(title=u"Relation")

We also define a class ``Item`` that implements both ``IItem``
and the special ``z3c.relationfield.interfaces.IHasRelations``
interface::

  >>> from z3c.relationfield.interfaces import IHasRelations
  >>> from persistent import Persistent
  >>> from zope.interface import implements
  >>> class Item(Persistent):
  ...   implements(IItem, IHasRelations)
  ...   def __init__(self):
  ...     self.rel = None

The ``IHasRelations`` marker interface is needed to let the relations
on ``Item`` be cataloged (when they are put in a container and removed
from it, for instance). It is in fact a combination of
``IHasIncomingRelations`` and ``IHasOutgoingRelations``, which is fine
as we want items to support both.

Finally we need a test application::

  >>> from zope.app.component.site import SiteManagerContainer
  >>> from zope.app.container.btree import BTreeContainer
  >>> class TestApp(SiteManagerContainer, BTreeContainer):
  ...   pass

We set up the test application::

  >>> root = getRootFolder()['root'] = TestApp()

We make sure that this is the current site, so we can look up local
utilities in it and so on. Normally this is done automatically by
Zope's traversal mechanism::

  >>> from zope.app.component.site import LocalSiteManager
  >>> root.setSiteManager(LocalSiteManager(root))
  >>> from zope.app.component.hooks import setSite
  >>> setSite(root)

For this site to work with ``z3c.relationship``, we need to set up two
utilities. Firstly, an ``IIntIds`` that tracks unique ids for objects
in the ZODB::

  >>> from zope.app.intid import IntIds
  >>> from zope.app.intid.interfaces import IIntIds
  >>> root['intids'] = intids = IntIds()
  >>> sm = root.getSiteManager()
  >>> sm.registerUtility(intids, provided=IIntIds)

And secondly a relation catalog that actually indexes the relations::

  >>> from z3c.relationfield import RelationCatalog
  >>> from zc.relation.interfaces import ICatalog
  >>> root['catalog'] = catalog = RelationCatalog()
  >>> sm.registerUtility(catalog, provided=ICatalog)

Using the relation field
========================

We'll add an item ``a`` to our application::

  >>> root['a'] = Item()

All items, including the one we just created, should have unique int
ids as this is required to link to them::

  >>> from zope import component
  >>> from zope.app.intid.interfaces import IIntIds
  >>> intids = component.getUtility(IIntIds)
  >>> a_id = intids.getId(root['a'])
  >>> a_id >= 0
  True

The relation is currently ``None``::

  >>> root['a'].rel is None
  True

Now we can create an item ``b`` that links to item ``a`` (through its
int id)::

  >>> from z3c.relationfield import RelationValue
  >>> b = Item()
  >>> b.rel = RelationValue(a_id)

We now store the ``b`` object in a container, which will also set up
its relation (as an ``IObjectAddedEvent`` will be fired)::

  >>> root['b'] = b

Let's examine the relation. First we'll check which attribute of the
pointing object ('b') this relation is pointing from::

  >>> root['b'].rel.from_attribute
  'rel'

We can ask for the object it is pointing at::

  >>> to_object = root['b'].rel.to_object
  >>> to_object.__name__
  u'a'

We can also get the object that is doing the pointing; since we
supplied the ``IHasRelations`` interface, the event system took care
of setting this::

  >>> from_object = root['b'].rel.from_object
  >>> from_object.__name__
  u'b'

This object is also known as the ``__parent__``; again the event
sytem took care of setting this::

  >>> parent_object = root['b'].rel.__parent__
  >>> parent_object is from_object
  True

The relation also knows about the interfaces of both the pointing object
and the object that is being pointed at::

  >>> from pprint import pprint
  >>> pprint(sorted(root['b'].rel.from_interfaces))
  [<InterfaceClass zope.location.interfaces.IContained>,
   <InterfaceClass z3c.relationfield.interfaces.IHasRelations>,
   <InterfaceClass __builtin__.IItem>,
   <InterfaceClass persistent.interfaces.IPersistent>]

  >>> pprint(sorted(root['b'].rel.to_interfaces))
  [<InterfaceClass zope.location.interfaces.IContained>,
   <InterfaceClass z3c.relationfield.interfaces.IHasRelations>,
   <InterfaceClass __builtin__.IItem>,
   <InterfaceClass persistent.interfaces.IPersistent>]

We can also get the interfaces in flattened form::

  >>> pprint(sorted(root['b'].rel.from_interfaces_flattened))
  [<InterfaceClass zope.location.interfaces.IContained>,
   <InterfaceClass z3c.relationfield.interfaces.IHasIncomingRelations>,
   <InterfaceClass z3c.relationfield.interfaces.IHasOutgoingRelations>,
   <InterfaceClass z3c.relationfield.interfaces.IHasRelations>,
   <InterfaceClass __builtin__.IItem>,
   <InterfaceClass zope.location.interfaces.ILocation>,
   <InterfaceClass persistent.interfaces.IPersistent>,
   <InterfaceClass zope.interface.Interface>]

  >>> pprint(sorted(root['b'].rel.to_interfaces_flattened))
  [<InterfaceClass zope.location.interfaces.IContained>,
   <InterfaceClass z3c.relationfield.interfaces.IHasIncomingRelations>,
   <InterfaceClass z3c.relationfield.interfaces.IHasOutgoingRelations>,
   <InterfaceClass z3c.relationfield.interfaces.IHasRelations>,
   <InterfaceClass __builtin__.IItem>,
   <InterfaceClass zope.location.interfaces.ILocation>,
   <InterfaceClass persistent.interfaces.IPersistent>,
   <InterfaceClass zope.interface.Interface>]

Paths
=====

We can also obtain the path of the relation (both from where it is
pointing as well as to where it is pointing). The path should be a
human-readable reference to the object we are pointing at, suitable
for serialization. In order to work with paths, we first need to set
up an ``IObjectPath`` utility.

Since in this example we only place objects into a single flat root
container, the paths in this demonstration can be extremely simple:
just the name of the object we point to. In more sophisticated
applications a path would typically be a slash separated path, like
``/foo/bar``::

  >>> from zope.interface import Interface
  >>> from zope.interface import implements
  >>> from z3c.objpath.interfaces import IObjectPath


  >>> class ObjectPath(object):
  ...
  ...     implements(IObjectPath)
  ...
  ...     def path(self, obj):
  ...         return obj.__name__
  ...     def resolve(self, path):
  ...         try:
  ...             return root[path]
  ...         except KeyError:
  ...             raise ValueError("Cannot resolve path %s" % path)

  >>> from zope.component import getGlobalSiteManager
  >>> gsm = getGlobalSiteManager()

  >>> op = ObjectPath()
  >>> gsm.registerUtility(op)


After this, we can get the path of the object the relation points to::

  >>> root['b'].rel.to_path
  u'a'

We can also get the path of the object that is doing the pointing::

  >>> root['b'].rel.from_path
  u'b'

Comparing and sorting relations
===============================

Let's create a bunch of ``RelationValue`` objects and compare them::

  >>> rel_to_a = RelationValue(a_id)
  >>> b_id = intids.getId(root['b'])
  >>> rel_to_b = RelationValue(b_id)
  >>> rel_to_a == rel_to_b
  False

Relations of course are equal to themselves::

  >>> rel_to_a == rel_to_a
  True

A relation that is stored is equal to a relation that isn't stored yet::

  >>> root['b'].rel == rel_to_a
  True

We can also sort relations::

  >>> [(rel.from_path, rel.to_path) for rel in
  ...  sorted([root['b'].rel, rel_to_a, rel_to_b])]
  [('', u'a'), ('', u'b'), (u'b', u'a')]



Relation queries
================

Now that we have set up and indexed a relationship between ``a`` and
``b``, we can issue queries using the relation catalog. Let's first
get the catalog::

  >>> from zc.relation.interfaces import ICatalog
  >>> catalog = component.getUtility(ICatalog)

Let's ask the catalog about the relation from ``b`` to ``a``::

  >>> l = sorted(catalog.findRelations({'to_id': intids.getId(root['a'])}))
  >>> l
  [<z3c.relationfield.relation.RelationValue object at ...>]

We look at this relation object again. We indeed go the right one::

  >>> rel = l[0]
  >>> rel.from_object.__name__
  u'b'
  >>> rel.to_object.__name__
  u'a'
  >>> rel.from_path
  u'b'
  >>> rel.to_path
  u'a'

Asking for relations to ``b`` will result in an empty list, as no such
relations have been set up::

  >>> sorted(catalog.findRelations({'to_id': intids.getId(root['b'])}))
  []

We can also issue more specific queries, restricting it on the
attribute used for the relation field and the interfaces provided by
the related objects. Here we look for all relations between ``b`` and
``a`` that are stored in object attribute ``rel`` and are pointing
from an object with interface ``IItem`` to another object with the
interface ``IItem``::

  >>> sorted(catalog.findRelations({
  ...   'to_id': intids.getId(root['a']),
  ...   'from_attribute': 'rel',
  ...   'from_interfaces_flattened': IItem,
  ...   'to_interfaces_flattened': IItem}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

There are no relations stored for another attribute::

  >>> sorted(catalog.findRelations({
  ...   'to_id': intids.getId(root['a']),
  ...   'from_attribute': 'foo'}))
  []

There are also no relations stored for a new interface we'll introduce
here::

  >>> class IFoo(IItem):
  ...   pass

  >>> sorted(catalog.findRelations({
  ...   'to_id': intids.getId(root['a']),
  ...   'from_interfaces_flattened': IItem,
  ...   'to_interfaces_flattened': IFoo}))
  []

Changing the relation
=====================

Let's create a new object ``c``::

  >>> root['c'] = Item()
  >>> c_id = intids.getId(root['c'])

Nothing points to ``c`` yet::

  >>> sorted(catalog.findRelations({'to_id': c_id}))
  []

We currently have a relation from ``b`` to ``a``::

  >>> sorted(catalog.findRelations({'to_id': intids.getId(root['a'])}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

We can change the relation to point at a new object ``c``::

  >>> root['b'].rel = RelationValue(c_id)

We need to send an ``IObjectModifiedEvent`` to let the catalog know we
have changed the relations::

  >>> from zope.event import notify
  >>> from zope.lifecycleevent import ObjectModifiedEvent
  >>> notify(ObjectModifiedEvent(root['b']))

We should find now a single relation from ``b`` to ``c``::

  >>> sorted(catalog.findRelations({'to_id': c_id}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

The relation to ``a`` should now be gone::

  >>> sorted(catalog.findRelations({'to_id': intids.getId(root['a'])}))
  []

Removing the relation
=====================

We have a relation from ``b`` to ``c`` right now::

  >>> sorted(catalog.findRelations({'to_id': c_id}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

We can clean up an existing relation from ``b`` to ``c`` by setting it
to ``None``::

  >>> root['b'].rel = None

We need to send an ``IObjectModifiedEvent`` to let the catalog know we
have changed the relations::

  >>> notify(ObjectModifiedEvent(root['b']))

Setting the relation on ``b`` to ``None`` should remove that relation
from the relation catalog, so we shouldn't be able to find it anymore::

  >>> sorted(catalog.findRelations({'to_id': intids.getId(root['c'])}))
  []

Let's reestablish the removed relation::

  >>> root['b'].rel = RelationValue(c_id)
  >>> notify(ObjectModifiedEvent(root['b']))

  >>> sorted(catalog.findRelations({'to_id': c_id}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

Copying an object with relations
================================

Let's copy an object with relations::

  >>> from zope.copypastemove.interfaces import IObjectCopier
  >>> IObjectCopier(root['b']).copyTo(root)
  u'b-2'
  >>> u'b-2' in root
  True

Two relations to ``c`` can now be found, one from the original, and
the other from the copy::

  >>> l = sorted(catalog.findRelations({'to_id': c_id}))
  >>> len(l)
  2
  >>> l[0].from_path
  u'b'
  >>> l[1].from_path
  u'b-2'

Relations are sortable
======================

Relations are sorted by default on a combination of the relation name,
the path of the object the relation is one and the path of the object
the relation is pointing to.

Let's query all relations availble right now and sort them::

  >>> l = sorted(catalog.findRelations())
  >>> len(l)
  2
  >>> l[0].from_attribute
  'rel'
  >>> l[1].from_attribute
  'rel'
  >>> l[0].from_path
  u'b'
  >>> l[1].from_path
  u'b-2'

Removing an object with relations
=================================

We will remove ``b-2`` again. Its relation should automatically be removed
from the catalog::

  >>> del root['b-2']
  >>> l = sorted(catalog.findRelations({'to_id': c_id}))
  >>> len(l)
  1
  >>> l[0].from_path
  u'b'

Breaking a relation
===================

We have a relation from ``b`` to ``c`` right now::

  >>> sorted(catalog.findRelations({'to_id': c_id}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

We have no broken relations::

  >>> sorted(catalog.findRelations({'to_id': None}))
  []

The relation isn't broken::

  >>> b.rel.isBroken()
  False

We are now going to break this relation by removing ``c``::

  >>> del root['c']

The relation is broken now::

  >>> b.rel.isBroken()
  True

The original relation still has a ``to_path``::

  >>> b.rel.to_path
  u'c'

It's broken however as there is no ``to_object``::

  >>> b.rel.to_object is None
  True

The ``to_id`` is also gone::

  >>> b.rel.to_id is None
  True

We cannot find the broken relation in the catalog this way as it's not
pointing to ``c_id`` anymore::

  >>> sorted(catalog.findRelations({'to_id': c_id}))
  []

We can however find it by searching for relations that have a
``to_id`` of ``None``::

  >>> sorted(catalog.findRelations({'to_id': None}))
  [<z3c.relationfield.relation.RelationValue object at ...>]

A broken relation isn't equal to ``None`` (this was a bug)::

  >>> b.rel == None
  False

RelationChoice
==============

A ``RelationChoice`` field is much like an ordinary ``Relation`` field
but can be used to render a special widget that allows a choice of
selections.

We will first demonstrate a ``RelationChoice`` field has the same effect
as a ``Relation`` field itself::

  >>> from z3c.relationfield import RelationChoice
  >>> class IChoiceItem(Interface):
  ...   rel = RelationChoice(title=u"Relation", values=[])
  >>> class ChoiceItem(Persistent):
  ...   implements(IChoiceItem, IHasRelations)
  ...   def __init__(self):
  ...     self.rel = None

Let's create an object to point the relation to::

  >>> root['some_object'] = Item()
  >>> some_object_id = intids.getId(root['some_object'])

And let's establish the relation::

  >>> choice_item = ChoiceItem()
  >>> choice_item.rel = RelationValue(some_object_id)
  >>> root['choice_item'] = choice_item

We can query for this relation now::

  >>> l = sorted(catalog.findRelations({'to_id': some_object_id}))
  >>> l
  [<z3c.relationfield.relation.RelationValue object at ...>]

RelationList
============

Let's now experiment with the ``RelationList`` field which can be used
to maintain a list of relations::

  >>> from z3c.relationfield import RelationList
  >>> class IMultiItem(Interface):
  ...   rel = RelationList(title=u"Relation")

We also define a class ``MultiItem`` that implements both
``IMultiItem`` and the special
``z3c.relationfield.interfaces.IHasRelations`` interface::

  >>> class MultiItem(Persistent):
  ...   implements(IMultiItem, IHasRelations)
  ...   def __init__(self):
  ...     self.rel = None

We set up a few object we can then create relations between::

  >>> root['multi1'] = MultiItem()
  >>> root['multi2'] = MultiItem()
  >>> root['multi3'] = MultiItem()

Let's create a relation from ``multi1`` to both ``multi2`` and
``multi3``::

  >>> multi1_id = intids.getId(root['multi1'])
  >>> multi2_id = intids.getId(root['multi2'])
  >>> multi3_id = intids.getId(root['multi3'])

  >>> root['multi1'].rel = [RelationValue(multi2_id),
  ...                       RelationValue(multi3_id)]

We need to notify that we modified the object

  >>> notify(ObjectModifiedEvent(root['multi1']))

Now that this is set up, let's verify whether we can find the
proper relations in in the catalog::

  >>> len(list(catalog.findRelations({'to_id': multi2_id})))
  1
  >>> len(list(catalog.findRelations({'to_id': multi3_id})))
  1
  >>> len(list(catalog.findRelations({'from_id': multi1_id})))
  2

Temporary relations
===================

If we have an import procedure where we import relations from some
external source such as an XML file, it may be that we read a relation
that points to an object that does not yet exist as it is yet to be
imported. We provide a special ``TemporaryRelationValue`` for this
case.  A ``TemporaryRelationValue`` just contains the path of what it
is pointing to, but does not resolve it yet. Let's use
``TemporaryRelationValue`` in a new object, creating a relation to
``a``::

  >>> from z3c.relationfield import TemporaryRelationValue
  >>> root['d'] = Item()
  >>> root['d'].rel = TemporaryRelationValue('a')

A modification event does not actually get this relation cataloged::

  >>> before = sorted(catalog.findRelations({'to_id': a_id}))
  >>> notify(ObjectModifiedEvent(root['d']))
  >>> after = sorted(catalog.findRelations({'to_id': a_id}))
  >>> len(before) == len(after)
  True

We will now convert all temporary relations on ``d`` to real ones::

  >>> from z3c.relationfield import realize_relations
  >>> realize_relations(root['d'])
  >>> notify(ObjectModifiedEvent(root['d']))

We can see the real relation object now::

  >>> root['d'].rel
  <z3c.relationfield.relation.RelationValue object at ...>

The relation will also now show up in the catalog::

  >>> after2 = sorted(catalog.findRelations({'to_id': a_id}))
  >>> len(after2) > len(before)
  True

Temporary relation values also work with ``RelationList`` objects::

  >>> root['multi_temp'] = MultiItem()
  >>> root['multi_temp'].rel = [TemporaryRelationValue('a')]

Let's convert this to a real relation::

  >>> realize_relations(root['multi_temp'])
  >>> notify(ObjectModifiedEvent(root['multi_temp']))

Again we can see the real relation object when we look at it::

  >>> root['multi_temp'].rel
  [<z3c.relationfield.relation.RelationValue object at ...>]

And we will now see this new relation appear in the catalog::

  >>> after3 = sorted(catalog.findRelations({'to_id': a_id}))
  >>> len(after3) > len(after2)
  True

Broken temporary relations
==========================

Let's create another temporary relation, this time a broken one that
cannot be resolved::

  >>> root['e'] = Item()
  >>> root['e'].rel = TemporaryRelationValue('nonexistent')

Let's try realizing this relation::

  >>> realize_relations(root['e'])

We end up with a broken relation::

  >>> root['e'].rel.isBroken()
  True

It's pointing to the nonexistent path::

  >>> root['e'].rel.to_path
  'nonexistent'
