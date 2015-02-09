=================
 Products.CMFUid
=================

.. contents::

CMFUid introduces a simple unique id implementation.

Implementation
==============

The supplied tools attach the unique ids to the objects. The objects
do not have to be aware of unique ids.

The current implementation depends on the portal catalog to find an 
object of a given unique id. The interfaces do not imply the use
of the catalog (except the IUniqueIdBrainQuery).

Which Tool does What?
=====================

The 'portal_uidgenerator' tools responsibility is to generate 
unique ids. The 'portal_uidannotation' tool is responsible to 
attach unique ids to a content object, and enforce rules about
what happens on object move/create/delete. The 'portal_uidhandler' 
manages registering and accessing unique ids. 

This design was chosen to allow users replacing only parts of
the functionality without having to understand the whole thing.

Unique Id API
=============

'portal_uidhandler' implementing 'IUniqueIdHandler' is the main 
API for playing with unique ids.
    
Usage
=====

'portal_uidhandler' fully implements IUniqueIdHandler (IUniqueIdSet
for registering/unregistering unique ids, IUniqueIdQuery for queries
and IUniqueIdBrainQuery for more efficient queries by returning 
catalog brains instead of objects).

The current implementation of get/queryBrain and get/queryObject 
do not return invisible objects (and brains of invisible objects).
By invisible objects, we mean objects that would be filtered out
by portal_catalog.searchResults due to expiry/effective date and/or
user roles.

It is often necessary to avoid this filtering in an application.
To do this, use the unrestrictedGet/QueryBrain and
unrestrictedGet/QueryObject as this will avoid 'None' results.

Have a look at the interfaces.

CMFUid's functionality is used by CMFDefault's favorite content type 
to follow linked objects. The favorite content type works as before if 
CMFUid is not installed. 


Update 2007-03-30
=================

The annotation code has been updated to use events for assigning/removing 
uids.  The settings for this live in the portal_uidannotation tool.

The default behaviour is:

- uids are NOT assigned when an object is created
  (it is assumed that other code is responsible for this)

- when an object is moved, a UID is not changed

- when an object is imported, any EXISTING UID is removed
  (this can be controlled via the 'remove_on_add' property)

- when an object is copied, any EXISTING UID is removed
  (this can be controlled via the 'remove_on_clone' property)

A more natural behaviour is for UIDs to be assigned automatically on 
creation.  To enable this feature:

- tick the 'assign UIDs on add' tickbox
  (uids will now be assigned when content is added or imported and any
  EXISTING uid will be replaced)

- tick the 'assign UIDs on copy' tickbox
  (objects will get a NEW uid when they are copied which will replace 
  any EXISTING uid)

In order to preserve the original behaviour of the tool, automatic 
assignment of uids is NOT enabled by default - it must be turned on in 
the uidannotation tool.

The behaviour is hooked in based on object creating/deletion/move events
for any IContentish objects.  The event handlers live in the 
UniqueIdAnnotation tool.

