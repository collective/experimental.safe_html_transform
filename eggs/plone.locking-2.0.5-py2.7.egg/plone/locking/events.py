from plone.locking.interfaces import ILockable

# These event handlers are not connected by default, but can be used for
# a particular object event (used e.g. in Archetypes)

def lockOnEditBegins(obj, event):
    """Lock the object when a user start working on the object
    """
    lockable = ILockable(obj)
    if not lockable.locked():
        lockable.lock()


def unlockAfterModification(obj, event):
    """Release the DAV lock after save
    """
    lockable = ILockable(obj)
    if lockable.can_safely_unlock():
        lockable.unlock()
