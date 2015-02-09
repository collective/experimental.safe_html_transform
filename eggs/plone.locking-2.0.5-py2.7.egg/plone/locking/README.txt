Tests
=====

Basic locking
-------------

By default, this is enabled on any ITTWLockable object. By default, this
applies to any Archetypes content object.

   >>> portal = layer['portal']

   >>> addMember(portal, 'member1', 'Member one')
   >>> addMember(portal, 'member2', 'Member two')
   >>> from Products.Archetypes.BaseContent import BaseContent
   >>> obj = BaseContent('id')
   >>> from plone.app.testing import login, logout
   >>> login(portal, 'member1')

To lock this object, we adapt it to ILockable. The default adapter implements
locking using WebDAV locks.

   >>> from plone.locking.interfaces import ILockable
   >>> lockable = ILockable(obj)

To begin with, this object will not be locked:

   >>> lockable.locked()
   False

We can then lock it:

   >>> lockable.lock()
   >>> lockable.locked()
   True

If we try to lock it again, nothing happens.

   >>> lockable.lock()
   >>> lockable.locked()
   True

We can get information about the lock as well:

   >>> info = lockable.lock_info()
   >>> len(info)
   1
   >>> info[0]['time'] > 0
   True
   >>> info[0]['creator']
   'member1'

We can refresh the lock so that its timeout is recalculated relative to the
current time.

  >>> old_lock_time = lockable.lock_info()[0]['time']
  >>> lockable.refresh_lock()
  >>> new_lock_time = lockable.lock_info()[0]['time']
  >>> new_lock_time > old_lock_time
  True

Once we have finished working on the object, we can unlock it.
   >>> lockable.unlock()
   >>> lockable.locked()
   False

There is no lock info when there is no lock:

    >>> lockable.lock_info()
    []

Stealable locks
---------------

By default, locks can be stolen. That is, if a particular user has a lock
and another user (with edit rights over the object) wants to edit the object,
the second user can unlock the object. This is opposed to "safe" unlocking,
which is done by the original owner.

Note that by convention, a user's own lock is "stealable" as well (kind of
like taking with the left hand and giving to the right).

    >>> lockable.lock()
    >>> lockable.can_safely_unlock()
    True
    >>> lockable.stealable()
    True

    >>> login(portal, 'member2')

    >>> lockable.locked()
    True
    >>> lockable.can_safely_unlock()
    False
    >>> lockable.stealable()
    True

    >>> lockable.unlock()
    >>> lockable.locked()
    False

Unlocked objects are "stealable" and can be safely unlocked, since calling
unlock() on an unlocked object has no effect.

    >>> lockable.stealable()
    True
    >>> lockable.can_safely_unlock()
    True

However, an object can be marked as having a non-stealable lock

    >>> from plone.locking.interfaces import INonStealableLock
    >>> from zope.interface import directlyProvides
    >>> directlyProvides(obj, INonStealableLock)

    >>> lockable.lock()

The owner of the lock is of course free to unlock

    >>> lockable.stealable()
    True
    >>> lockable.unlock()
    >>> lockable.locked()
    False

Another user is not, and unlock() has no effect.

    >>> lockable.lock()
    >>> lockable.locked()
    True

    >>> login(portal, 'member1')

    >>> lockable.stealable()
    False
    >>> lockable.unlock()
    >>> lockable.locked()
    True

    >>> from zope.interface import noLongerProvides
    >>> noLongerProvides(obj, INonStealableLock)
    >>> lockable.clear_locks()
    >>> lockable.locked()
    False

Categorised locks
-----------------

So far, we have been managing a single type of lock. However, it is possible
to manage different types of locks which are mutually exclusive. For example,
if a particular type of lock is applied, it cannot be stolen by a user who
is attempting to create another type of lock.

Consider the default type of lock:

    >>> from plone.locking.interfaces import STEALABLE_LOCK

This is simply a string that represents the default "stealable" locks. Let's
consider a check-in/check-out stating system that needs to lock the baseline
copy of an object when a working copy is checked out:

    >>> from plone.locking.interfaces import LockType
    >>> COCI_LOCK = LockType(u'coci.lock', stealable=False, user_unlockable=False)

This is a very restrictive lock - it cannot be stolen or unlocked by the
user. If we lock with this lock type, no-one can steal or safely unlock
the object, regardless of lock type.

    >>> lockable.lock(COCI_LOCK)
    >>> lockable.locked()
    True

    >>> lockable.can_safely_unlock()
    False
    >>> lockable.can_safely_unlock(COCI_LOCK)
    False

    >>> lockable.stealable()
    False
    >>> lockable.stealable(COCI_LOCK)
    False

    >>> lockable.unlock(COCI_LOCK)
    >>> lockable.locked()
    False

Now consider a lock that is stealable, but distinct from the regular stealable
lock. In this case, code managing one type of lock cannot steal locks or
safely unlock objects locked with the other:

    >>> SPECIAL_LOCK = LockType(u'special.lock', stealable=True, user_unlockable=True)
    >>> lockable.lock(SPECIAL_LOCK)
    >>> lockable.locked()
    True

    >>> lockable.can_safely_unlock()
    False
    >>> lockable.can_safely_unlock(SPECIAL_LOCK)
    True

    >>> lockable.stealable()
    False
    >>> lockable.stealable(SPECIAL_LOCK)
    True

    >>> lockable.unlock()
    >>> lockable.locked()
    True
    >>> lockable.unlock(SPECIAL_LOCK)
    >>> lockable.locked()
    False


Anonymous locking
=================

When we are anonymous but do have edit rights we can also do a lock.

   >>> logout()
   >>> lockable.lock()
   >>> lockable.locked()
   True

   >>> info = lockable.lock_info()
   >>> len(info)
   1
   >>> info[0]['time'] > 0
   True
   >>> info[0]['creator'] is None
   True

Locking timeouts
================

Lock timeout should be ten minutes by default

    >>> token = info[0]['token']
    >>> lock = lockable.context.wl_getLock(token)
    >>> lock._timeout
    600L

Turning locking on or off
=========================

The status of the entire TTW locking mechanism can be controlled by setting
up an ILockSettings adapter with a lock_on_ttw_edit property.

    >>> class DummyLockSettings(object):
    ...     def __init__(self, context):
    ...         self.context = context
    ...     lock_on_ttw_edit = False
    >>> from zope.component import getGlobalSiteManager
    >>> from plone.locking.interfaces import ITTWLockable, ILockSettings
    >>> gsm = getGlobalSiteManager()
    >>> gsm.registerAdapter(DummyLockSettings, required=(ITTWLockable,), provided=ILockSettings)

Now trying to lock the object should have no effect.

    >>> lockable.unlock()
    >>> lockable.locked()
    False
    >>> lockable.lock()
    >>> lockable.locked()
    False

But if the property is True, then locking should function again.

    >>> DummyLockSettings.lock_on_ttw_edit = True
    >>> lockable.lock()
    >>> lockable.locked()
    True

Clean up.

    >>> gsm.unregisterAdapter(DummyLockSettings, required=(ITTWLockable,), provided=ILockSettings)
    True
