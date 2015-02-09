##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit at www.openplans.org>
#   - and contributors
#
##########################################################
from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import OOBTree
from wicked.interfaces import ICacheManager, IAmWicked, IWickedFilter
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from zope.component import adapts
from utils import memoizedproperty, clearbefore

_marker = object()

# @@ need sys-module alias


class CacheStore(Persistent):
    """
    basic persistent cache object

    see cache.txt
    """
    def __init__(self, id_):
        self.id = id_
        self.field={}
        self._cache = OOBTree()

    def __repr__(self):
        name = self.__class__.__name__
        name = "%s '%s'" %(name, self.id)
        return "%s %s :: %s" %(name, self.field, [x for x in self._cache.items()])

    def get(self, key, default=None):
        return self._cache.get(key, default)

    def set(self, key, value):
        self._cache[key] = value
        self._p_changed

    def getCache(self, key):
        subcache = self.field.get(key, _marker)
        if subcache is _marker:
            cache = Cache(parent=self, id_=self.id)
            self.field[key] = cache
            subcache = self.field[key]
            self._p_changed
        return subcache

    def remove(self, key):
        val = self._cache.get(key)
        if val:
            del self._cache[key]
            self._p_changed=True
            for name, fcache in self.field.items():
                for slug, uid in fcache.items():
                    if uid==key:
                        del fcache[slug]


class Cache(PersistentMapping):

    def __init__(self, id_=None, parent=None):
        self.parent = parent
        self.id = id_
        self._reverse={}
        super(Cache, self).__init__()

    def getRaw(self, key):
        return super(Cache, self).__getitem__(key)

    def parentGet(self, uid, default=None):
        return self.parent.get(str(uid), default)

    def get(self, key, default=None):
        uid = super(Cache, self).get(key, default)
        return self.parentGet(uid, default)

    def set(self, key, value):
        slug, uid = key
        self[slug] = uid
        self._reverse[uid] = slug
        self.parent.set(uid, value)
        self._p_changed
        return value

    def __getitem__(self, key):
        retval = self.parentGet(key)
        if retval: return retval
        return self.getRaw(key)

    def __repr__(self):
        rep = super(Cache, self).__repr__()
        name = self.__class__.__name__
        name = "%s '%s'" %(name, self.id)
        return "%s %s" %(name, rep)

    def __delitem__(self, key):
        """
        trickle up deletion
        """
        self.parent.remove(key)
        super(Cache, self).__delitem__(key)

# @@ migrate to new name
CACHE_KEY = 'Products.wicked.lib.factories.ContentCacheManager'

class BaseCacheManager(object):
    """abstract base"""
    implements(ICacheManager)
    adapts(IWickedFilter, IAmWicked)

    def __init__(self, wicked, context):
        self.context = context
        self.name = wicked.section

    @clearbefore
    def setName(self, name):
        self.name = name

    @memoizedproperty
    def cache_store(self):
        raise NotImplementedError

    def _get_cache(self, name=None):
        if not name:
            name = self.name
        cache = self.cache_store.getCache(name)
        return cache

    @memoizedproperty
    def cache(self):
        return self._get_cache()

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def set(self, key, value):
        self.cache.set(key, value)
        return value

    def unset(self, key, use_uid=False):
        val = None
        if use_uid:
            for tkey, uid in self.cache.items():
                if uid == key:
                    val = self.get(tkey)
                    del self.cache[tkey]

        if self.cache.has_key(key):
            val = self.get(key)
            del self.cache[key]

        return val

    def remove(self, uid):
        self.cache_store.remove(uid)

    def reset(self, uid, value):
        self.cache_store.set(uid, value)


class ContentCacheManager(BaseCacheManager):

    @memoizedproperty
    def cache_store(self):
        ann = IAnnotations(self.context)
        cache_store = ann.get(CACHE_KEY)
        if not cache_store:
            cache_store = CacheStore(id_='/'.join(self.context.getPhysicalPath()))
            ann[CACHE_KEY] = cache_store
        return cache_store



