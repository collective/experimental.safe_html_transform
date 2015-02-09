Usage
=====

First, let make sure the ofs utility provides the interface::

    >>> from Products.Five.tests.testing.simplecontent import (
    ...   manage_addSimpleContent)

    >>> from zope.intid.interfaces import IIntIds
    >>> from five.intid import site
    >>> import five.intid.tests as tests
    >>> from zope.interface.verify import verifyObject
    >>> from zope.component import getAllUtilitiesRegisteredFor
    >>> from zope.site.hooks import setSite
    >>> tests.setUp(self.app)


Content added before the utility won't be registered (until explicitly
called to). We'll set some up now for later

    >>> manage_addSimpleContent(self.folder, 'mycont1', "My Content")
    >>> content1 = self.folder.mycont1

`five.intid.site` has convenience functions for adding, get and
removing an IntId utility: `add_intid`, `get_intid`, `del_intid`.

You can install the utility in a specific location::

    >>> site.add_intids(self.folder)
    >>> folder_intids = site.get_intids(self.folder)
    >>> verifyObject(IIntIds, folder_intids)
    True

You can tell `add_intids` to find the site root, and install there.
It will be available everywhere::

    >>> site.add_intids(self.folder, findroot=True)
    >>> root_intids = site.get_intids(self.app)
    >>> root_intids
    <...IntIds ...>
    >>> folder_intids is root_intids
    False

And finally, do a remove::

    >>> site.del_intids(self.folder, findroot=True)
    >>> site.get_intids(self.app)
    Traceback (most recent call last):
    ...
    ComponentLookupError: (<InterfaceClass ....IIntIds>, '')

Before we look at intid events, we need to set the traversal
hook. Once we have done this, when we ask for all registered Intids,
we will get the utility from test folder::

    >>> setSite(self.folder)
    >>> tuple(getAllUtilitiesRegisteredFor(IIntIds))
    (<...IntIds ...>,)


When we add content, event will be fired to add keyreference for said
objects the utilities (currently, our content and the utility are
registered)::

    >>> manage_addSimpleContent(self.folder, 'mycont2', "My Content")
    >>> content2 = self.folder.mycont2
    >>> intid = site.get_intids(self.folder)
    >>> len(intid.items()) == 1
    True

Pre-existing content will raise a keyerror if passed to the intid
utility::

    >>> intid.getId(content1)
    Traceback (most recent call last):
    ...
    KeyError: <SimpleContent at /test_folder_1_/mycont1>

We can call the keyreferences, and get the objects back::

    >>> intid.items()[0][1]()
    <SimpleContent at /test_folder_1_/mycont2>

we can get an object's `intid` from the utility like so::

    >>> ob_id = intid.getId(content2)

and get an object back like this::

    >>> intid.getObject(ob_id)
    <SimpleContent at /test_folder_1_/mycont2>

these objects are aquisition wrapped on retrieval::

    >>> from Acquisition import IAcquirer
    >>> IAcquirer.providedBy(intid.getObject(ob_id))
    True


We can even turn an unwrapped object into a wrapped object by
resolving it from it's intid, also the intid utility should work
even if it is unwrapped::

    >>> from Acquisition import aq_base
    >>> resolved = intid.getObject(intid.getId(aq_base(content2)))
    >>> IAcquirer.providedBy(resolved)
    True
    >>> unwrapped = aq_base(intid)
    >>> unwrapped.getObject(ob_id) == resolved
    True
    >>> unwrapped.getId(content2) == ob_id
    True

When an object is added or removed, subscribers add it to the intid
utility, and fire an event is fired
(zope.intid.interfaces.IIntIdAddedEvent,
zope.intid.interfaces.IIntIdRemovedEvent respectively).

`five.intid` hooks up these events to redispatch as object events. The
tests hook up a simple subscriber to verify that the intid object
events are fired (these events are useful for catalogish tasks).

    >>> tests.NOTIFIED[0]
    '<SimpleContent at mycont2> <...IntIdAddedEvent object at ...'

Registering and unregistering objects does not fire these events::

    >>> tests.NOTIFIED[0] = "No change"
    >>> uid = intid.register(content1)
    >>> intid.getObject(uid)
    <SimpleContent at /test_folder_1_/mycont1>

    >>> tests.NOTIFIED[0]
    'No change'

    >>> intid.unregister(content1)
    >>> intid.getObject(uid)
    Traceback (most recent call last):
    ...
    KeyError: ...

    >>> tests.NOTIFIED[0]
    'No change'

Renaming an object should not break the rewrapping of the object:

    >>> self.setRoles(['Manager'])
    >>> folder.mycont2.meta_type = 'Folder' # We need a metatype to move
    >>> folder.manage_renameObject('mycont2','mycont_new')
    >>> moved = intid.getObject(ob_id)
    >>> moved
    <SimpleContent at /test_folder_1_/mycont_new>

Nor should moving it:

    >>> from OFS.Folder import manage_addFolder
    >>> manage_addFolder(self.folder, 'folder2', "folder 2")
    >>> cut = folder.manage_cutObjects(['mycont_new'])
    >>> ignore = folder.folder2.manage_pasteObjects(cut)
    >>> moved = intid.getObject(ob_id)
    >>> moved
    <SimpleContent at /test_folder_1_/folder2/mycont_new>
    >>> moved.aq_parent
    <Folder at /test_folder_1_/folder2>

Let's move it back:

    >>> cut = folder.folder2.manage_cutObjects(['mycont_new'])
    >>> ignore = folder.manage_pasteObjects(cut)
    >>> folder.manage_renameObject('mycont_new','mycont2')

We can create an object without acquisition so we can be able to
add intid to it :

    >>> from five.intid.tests import DemoPersistent
    >>> demo1 = DemoPersistent()
    >>> demo1.__parent__ = self.app
    >>> from zope.event import notify
    >>> from zope.lifecycleevent import ObjectAddedEvent
    >>> notify(ObjectAddedEvent(demo1))
    >>> nowrappid = intid.getId(demo1)
    >>> demo1 == intid.getObject(nowrappid)
    True

This is a good time to take a look at keyreferences, the core part of
this system.


Key References in Zope2
=======================

Key references are hashable objects returned by IKeyReference.  The
hash produced is a unique identifier for whatever the object is
referencing(another zodb object, a hook for sqlobject, etc).

object retrieval in intid occurs by calling a key reference. This
implementation is slightly different than the zope.intid one due to
acquisition.

The factories returned by IKeyReference must persist and this dictates
being especially careful about references to acquisition wrapped
objects as well as return acq wrapped objects as usually expected in
zope2.

    >>> ref = intid.refs[ob_id]
    >>> ref
    <five.intid.keyreference.KeyReferenceToPersistent object at ...>

The reference object holds a reference to the unwrapped target object
and a property to fetch the app(also, not wrapped ie <type 'ImplicitAcquirerWrapper'>)::

    >>> ref.object
    <SimpleContent at mycont2>

    >>> type(ref.object)
    <class 'Products.Five.tests.testing.simplecontent.SimpleContent'>

    >>> ref.root
    <Application at >

Calling the reference object (or the property wrapped_object) will
return an acquisition object wrapped object (wrapped as it was
created)::

    >>> ref.wrapped_object == ref()
    True

    >>> ref()
    <SimpleContent at /test_folder_1_/mycont2>

    >>> IAcquirer.providedBy(ref())
    True



The resolution mechanism tries its best to end up with the current
request at the end of the acquisition chain, just as it would be
under normal circumstances::

    >>> ref.wrapped_object.aq_chain[-1]
    <ZPublisher.BaseRequest.RequestContainer object at ...>


The hash calculation is a combination of the database name and the
object's persistent object id(oid)::

    >>> ref.dbname
    'unnamed'

    >>> hash((ref.dbname, ref.object._p_oid)) == hash(ref)
    True

    >>> tests.tearDown()

Acquisition Loops
=================

five.intid detects loops in acquisition chains in both aq_parent and
__parent__.

Setup a loop::

    >>> import Acquisition
    >>> class Acq(Acquisition.Acquirer): pass
    >>> foo = Acq()
    >>> foo.bar = Acq()
    >>> foo.__parent__ = foo.bar

Looking for the root on an object with an acquisition loop will raise
an error::

    >>> from five.intid import site
    >>> site.get_root(foo.bar)
    Traceback (most recent call last):
    ...
    AttributeError: __parent__ loop found

Looking for the connection on an object with an acquisition loop will
simply return None::

    >>> from five.intid import keyreference
    >>> keyreference.connectionOfPersistent(foo.bar)

Unreferenceable
===============

Some objects implement IPersistent but are never actually persisted, or
contain references to such objects. Specifically, CMFCore directory views
contain FSObjects that are never persisted, and DirectoryViewSurrogates
that contain references to such objects. Because FSObjects are never actually
persisted, five.intid's assumption that it can add a

For such objects, the unreferenceable module provides no-op subcribers and
adapters to omit such objects from five.intid handling.

    >>> from zope import interface, component
    >>> from five.intid import unreferenceable

    >>> from Products.CMFCore import FSPythonScript
    >>> foo = FSPythonScript.FSPythonScript('foo', __file__)
    >>> self.app._setObject('foo', foo)
    'foo'

    >>> keyref = unreferenceable.KeyReferenceNever(self.app.foo)
    Traceback (most recent call last):
    ...
    NotYet
    >>> foo in self.app._p_jar._registered_objects
    False

Objects with no id
==================

It is possible to attempt to get a key reference for an object that has not
yet been properly added to a container, but would otherwise have a path.
In this case, we raise the NotYet exception to let the calling code defer
as necessary, since the key reference would otherwise resolve the wrong
object (the parent, to be precise) from an incorrect path.

    >>> from zope.keyreference.interfaces import IKeyReference
    >>> from five.intid.keyreference import KeyReferenceToPersistent
    >>> from zope.component import provideAdapter
    >>> provideAdapter(KeyReferenceToPersistent)

    >>> from OFS.SimpleItem import SimpleItem
    >>> item = SimpleItem('').__of__(self.folder)
    >>> '/'.join(item.getPhysicalPath())
    '/test_folder_1_/'

    >>> IKeyReference(item)
    Traceback (most recent call last):
    ...
    NotYet: <SimpleItem at >


If the object is placed in a circular containment, IKeyReference(object) should
also raise an NotYet Error, letting the calling code defer as neccesary.
This case happend when having a Plone4 site five.intrd enabled
(five.intid.site.add_intids(site)) and trying to add a portlet via
@@manage-portlets. plone.portlet.static.static.Assignment seems to have a
circular path at some time.

Creating items whith a circular containment
    >>> item_b = SimpleItem().__of__(self.folder)
    >>> item_b.id = "b"
    >>> item_c = SimpleItem().__of__(item_b)
    >>> item_c.id = "c"
    >>> item_b.__parent__ = item_c

    >>> assert item_b.__parent__.__parent__ == item_b

    >>> IKeyReference(item_c)
    Traceback (most recent call last):
    ...
    NotYet: <SimpleItem at c>

