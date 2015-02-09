from zope.interface import implements, Interface, Attribute
from zope.annotation.interfaces import IAttributeAnnotatable

from zope import schema

# Lock types, including the default

# Timeouts are expressed in minutes
DEFAULT_TIMEOUT = 10L
MAX_TIMEOUT = ((2L ** 32) - 1) / 60


class ILockType(Interface):
    """Representation of a type of lock
    """

    __name__ = schema.TextLine(title=u"Name",
                               description=u"The unique name of the lock type")

    stealable = schema.Bool(title=u"Stealable",
                            description=u"Whether this type of lock is stealable")
    user_unlockable = schema.Bool(title=u"User unlockable",
                                  description=u"Whether this type of lock should be unlockable immediately")
    timeout = schema.Int(title=u"lock timeout",
                         description=u"Locking timeout in minutes")


class LockType(object):
    implements(ILockType)

    def __init__(self, name, stealable, user_unlockable, timeout=DEFAULT_TIMEOUT):
        self.__name__ = name
        self.stealable = stealable
        self.user_unlockable = user_unlockable
        self.timeout = timeout

STEALABLE_LOCK = LockType(u"plone.locking.stealable", stealable=True, user_unlockable=True)

# Marker interfaces

class ITTWLockable(IAttributeAnnotatable):
    """Marker interface for objects that are lockable through-the-web
    """


class INonStealableLock(Interface):
    """Mark an object with this interface to make locks be non-stealable.
    """

# Functionality

class ILockable(Interface):
    """A component that is lockable.

    Lock tokens are remembered (in annotations). Multiple locks can exist,
    based on lock types. The default lock type, STEALABLE_LOCK, is a lock
    that can be stolen (unless the object is marked with INonStealableLock).

    Most operations take the type as a parameter and operate on the lock token
    assocaited with a particular type.
    """

    def lock(lock_type=STEALABLE_LOCK, children=False):
        """Lock the object using the given key.

        If children is True, child objects will be locked as well.
        """

    def unlock(lock_type=STEALABLE_LOCK, stealable_only=True):
        """Unlock the object using the given key.

        If stealable_only is true, the operation will only have an effect on
        objects that are stealable(). Thus, non-stealable locks will need
        to pass stealable_only=False to actually get unlocked.
        """

    def clear_locks():
        """Clear all locks on the object
        """

    def locked():
        """True if the object is locked with any lock.
        """

    def can_safely_unlock(lock_type=STEALABLE_LOCK):
        """Determine if the current user can safely attempt to unlock the
        object.

        That means:

         - lock_type.user_unlockable is True; and

         - the object is not locked; or
         - the object is only locked with the given lock_type, for the
           current user;
        """

    def stealable(lock_type=STEALABLE_LOCK):
        """Find out if the lock can be stolen.

        This means:

         - the lock type is stealable; and

         - the object is not marked with INonStealableLock; or
         - can_safely_unlock() is true.

        """

    def lock_info():
        """Get information about locks on object.

        Returns a list containing the following dict for each valid lock:

         - creator : the username of the lock creator
         - time    : the time at which the lock was acquired
         - token   : the underlying lock token
         - type    : the type of lock
        """


class IRefreshableLockable(ILockable):
    """ A component that is lockable and whose locks can be refreshed.
    """

    def refresh_lock(lock_type=STEALABLE_LOCK):
        """Refresh the lock so it expires later.
        """

# Configuration

class ILockSettings(Interface):
    """A component that looks up configuration settings for lock behavior.
    """
    lock_on_ttw_edit = Attribute('A property that reveals whether '
                                 'through-the-web locking is enabled.')
