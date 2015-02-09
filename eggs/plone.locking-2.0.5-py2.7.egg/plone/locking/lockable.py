from zope.interface import implements
from zope.component import adapts, queryAdapter

from persistent.dict import PersistentDict

from zope.annotation.interfaces import IAnnotations

from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from webdav.LockItem import LockItem

from plone.locking.interfaces import IRefreshableLockable
from plone.locking.interfaces import INonStealableLock
from plone.locking.interfaces import ITTWLockable
from plone.locking.interfaces import STEALABLE_LOCK
from plone.locking.interfaces import ILockSettings

ANNOTATION_KEY = 'plone.locking'


class TTWLockable(object):
    """An object that is being locked through-the-web
    """

    implements(IRefreshableLockable)
    adapts(ITTWLockable)

    def __init__(self, context):
        self.context = context
        self.__locks = None

    def lock(self, lock_type=STEALABLE_LOCK, children=False):
        settings = queryAdapter(self.context, ILockSettings)
        if settings is None:
            # No context specific adapter, is this a Plone site?
            pprops = getToolByName(self.context, 'portal_properties', None)
            if pprops is not None and 'site_properties' in pprops.objectIds():
                settings = pprops.site_properties
        if settings is not None and settings.lock_on_ttw_edit is False:
            return

        if not self.locked():
            user = getSecurityManager().getUser()
            depth = children and 'infinity' or 0
            lock = LockItem(user, depth=depth, timeout=lock_type.timeout * 60L)
            token = lock.getLockToken()
            self.context.wl_setLock(token, lock)

            self._locks()[lock_type.__name__] = dict(type=lock_type,
                                                  token=token)

    def refresh_lock(self, lock_type=STEALABLE_LOCK):
        if not self.locked():
            return

        key = self._locks().get(lock_type.__name__, None)
        if key:
            lock = self.context.wl_getLock(key['token'])
            lock.refresh()

    def unlock(self, lock_type=STEALABLE_LOCK, stealable_only=True):
        if not self.locked():
            return

        if not lock_type.stealable or not stealable_only \
           or self.stealable(lock_type):
            key = self._locks().get(lock_type.__name__, None)
            if key:
                self.context.wl_delLock(key['token'])
                del self._locks()[lock_type.__name__]

    def clear_locks(self):
        self.context.wl_clearLocks()
        self._locks().clear()

    def locked(self):
        if self.lock_info():
            return True
        else:
            return False

    def can_safely_unlock(self, lock_type=STEALABLE_LOCK):
        if not lock_type.user_unlockable:
            return False

        info = self.lock_info()
        # There is no lock, so return True
        if len(info) == 0:
            return True

        userid = getSecurityManager().getUser().getId() or None
        for l in info:
            # There is another lock of a different type
            if not hasattr(l['type'], '__name__') or \
               l['type'].__name__ != lock_type.__name__:
                return False
            # The lock is in fact held by the current user
            if l['creator'] == userid:
                return True
        return False

    def stealable(self, lock_type=STEALABLE_LOCK):
        # If the lock type is not stealable ever, return False
        if not lock_type.stealable:
            return False
        # Can't steal locks of a different type
        for l in self.lock_info():
            if not hasattr(l['type'], '__name__') or \
               l['type'].__name__ != lock_type.__name__:
                return False
        # The lock type is stealable, and the object is not marked as
        # non-stelaable, so return True
        if not INonStealableLock.providedBy(self.context):
            return True
        # Lock type is stealable, object is not stealable, but return True
        # anyway if we can safely unlock this object (e.g. we are the owner)
        return self.can_safely_unlock(lock_type)

    def lock_info(self):
        info = []
        rtokens = dict([(v['token'], v['type']) for v in self._locks(False).values()])
        jar = self.context._p_jar
        if jar is not None:
            isReadOnly = jar.isReadOnly()
        else:
            isReadOnly = False
        for lock in self.context.wl_lockValues(not isReadOnly):
            if not lock.isValid():
                continue  # Skip invalid/expired locks
            token = lock.getLockToken()
            creator = lock.getCreator()
            # creator can be None when locked by an anonymous user
            if creator is not None:
                creator = creator[1]
            info.append({
                'creator': creator,
                'time': lock.getModifiedTime(),
                'token': token,
                'type': rtokens.get(token, None),
            })
        return info

    def _locks(self, create=True):
        if self.__locks is not None:
            return self.__locks

        annotations = IAnnotations(self.context)
        locks = annotations.get(ANNOTATION_KEY, None)
        if locks is None and create:
            locks = annotations.setdefault(ANNOTATION_KEY, PersistentDict())
        if locks is not None:
            self.__locks = locks
            return self.__locks
        else:
            return {}
