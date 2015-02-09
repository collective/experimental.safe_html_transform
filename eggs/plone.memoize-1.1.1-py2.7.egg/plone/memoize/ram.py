"""A cache decorator that uses RAMCache by default.

See README.txt and the `volatile` module for more details.

  >>> def cache_key(fun, first, second):
  ...     return (first, second)
  >>> @cache(cache_key)
  ... def pow(first, second):
  ...     print 'Someone or something called me'
  ...     return first ** second

  >>> pow(3, 2)
  Someone or something called me
  9
  >>> pow(3, 2)
  9

Let's cache another function:

  >>> @cache(cache_key)
  ... def add(first, second):
  ...     print 'Someone or something called me'
  ...     return first + second

  >>> add(3, 2)
  Someone or something called me
  5
  >>> add(3, 2)
  5

Now invalidate the cache for the `pow` function:

  >>> pow(3, 2)
  9
  >>> global_cache.invalidate('plone.memoize.ram.pow')
  >>> pow(3, 2)
  Someone or something called me
  9

Make sure that we only invalidated the cache for the `pow` function:

  >>> add(3, 2)
  5

  >>> global_cache.invalidateAll()

You can register an ICacheChooser utility to override the cache used
based on the function that is cached.  To do this, we'll first
unregister the already registered global `choose_cache` function:

  >>> sm = component.getGlobalSiteManager()
  >>> sm.unregisterUtility(choose_cache)
  True

This customized cache chooser will use the `my_cache` for the `pow`
function, and use the `global_cache` for all other functions:

  >>> my_cache = ram.RAMCache()
  >>> def my_choose_cache(fun_name):
  ...     if fun_name.endswith('.pow'):
  ...         return RAMCacheAdapter(my_cache)
  ...     else:
  ...         return RAMCacheAdapter(global_cache)
  >>> interface.directlyProvides(my_choose_cache, ICacheChooser)
  >>> sm.registerUtility(my_choose_cache)

Both caches are empty at this point:

  >>> len(global_cache.getStatistics())
  0
  >>> len(my_cache.getStatistics())
  0

Let's fill them:

  >>> pow(3, 2)
  Someone or something called me
  9
  >>> pow(3, 2)
  9
  >>> len(global_cache.getStatistics())
  0
  >>> len(my_cache.getStatistics())
  1

  >>> add(3, 2)
  Someone or something called me
  5
  >>> add(3, 2)
  5
  >>> len(global_cache.getStatistics())
  1
  >>> len(my_cache.getStatistics())
  1
"""

import cPickle

from zope import interface
from zope import component
from zope.ramcache.interfaces.ram import IRAMCache
from zope.ramcache import ram

from plone.memoize.interfaces import ICacheChooser
from plone.memoize import volatile

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5


global_cache = ram.RAMCache()
global_cache.update(maxAge=86400)

DontCache = volatile.DontCache
MARKER = object()


class AbstractDict:

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


class MemcacheAdapter(AbstractDict):

    def __init__(self, client, globalkey=''):
        self.client = client
        self.globalkey = globalkey and '%s:' % globalkey

    def _make_key(self, source):
        if isinstance(source, unicode):
            source = source.encode('utf-8')
        return md5(source).hexdigest()

    def __getitem__(self, key):
        cached_value = self.client.get(self.globalkey + self._make_key(key))
        if cached_value is None:
            raise KeyError(key)
        else:
            return cPickle.loads(cached_value)

    def __setitem__(self, key, value):
        cached_value = cPickle.dumps(value)
        self.client.set(self.globalkey + self._make_key(key), cached_value)


class RAMCacheAdapter(AbstractDict):

    def __init__(self, ramcache, globalkey=''):
        self.ramcache = ramcache
        self.globalkey = globalkey

    def _make_key(self, source):
        if isinstance(source, unicode):
            source = source.encode('utf-8')
        return md5(source).digest()

    def __getitem__(self, key):
        value = self.ramcache.query(self.globalkey,
                                    dict(key=self._make_key(key)),
                                    MARKER)
        if value is MARKER:
            raise KeyError(key)
        else:
            return value

    def __setitem__(self, key, value):
        self.ramcache.set(value,
                          self.globalkey,
                          dict(key=self._make_key(key)))


def choose_cache(fun_name):
    return RAMCacheAdapter(component.queryUtility(IRAMCache),
                           globalkey=fun_name)
interface.directlyProvides(choose_cache, ICacheChooser)


def store_in_cache(fun, *args, **kwargs):
    key = '%s.%s' % (fun.__module__, fun.__name__)
    cache_chooser = component.queryUtility(ICacheChooser)
    if cache_chooser is not None:
        return cache_chooser(key)
    else:
        return RAMCacheAdapter(global_cache, globalkey=key)


def cache(get_key):
    return volatile.cache(get_key, get_cache=store_in_cache)
