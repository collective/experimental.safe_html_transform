Introduction
============

plone.memoize provides Python function decorators for caching the
values of functions and methods.

The type of cache storage is freely configurable by the user, as is
the cache key, which is what the function's value depends on.

plone.memoize has support for memcached and is easily extended to use
other caching storages.  It also has specialized decorators for use
with Zope views.  However, plone.memoize can be used without Zope.


volatile
========

The 'volatile' module defines a versatile caching decorator that gives
you total control of how the cache key is calculated and where it is
stored.  This decorator is explained in more in depth with example
usage in 'volatile.py'.

'volatile' caches can be stored in different places. A common use is
a zope RAMCache. There are convenience methods in the 'ram' module
to support that.

A quick example of a view that uses 'volatile' caching through the 'ram'
module:

  >>> from zope.publisher.browser import BrowserView
  >>> from plone.memoize import ram

  >>> def _render_details_cachekey(method, self, brain):
  ...    return (brain.getPath(), brain.modified)

  >>> class View(BrowserView):
  ...    @ram.cache(_render_details_cachekey)
  ...    def render_details(self, brain):
  ...        obj = brain.getObject()
  ...        view = obj.restrictedTraverse('@@obj-view')
  ...        return view.render()

The results of our hypothetical 'render_details' method are cached
*across requests* and independently of the (not) logged in user.  The
cache is only refreshed when the brain's path or modification date
change, as defined in '_render_details_cachekey'.

This is how you could use the same decorator to cache a function's
value for an hour:

  >>> from time import time
  >>> @ram.cache(lambda *args: time() // (60 * 60))
  ... def fun():
  ...     return "Something that takes awfully long"
  >>> fun()
  'Something that takes awfully long'


view and instance
=================

See view.txt and instance.txt for usage of cache decorators that have
a fixed cache key and cache storage.  The most common usage pattern of
these view and instance caching decorators is:

 >>> from plone.memoize import instance
 >>> class MyClass(object):
 ...   @instance.memoize
 ...   def some_expensive_function(self, arg1, arg2):
 ...       return "Some expensive result"

The first time some_expensive_function() is called, the return value will
be saved. On subsequent calls with the same arguments, the cached version
will be returned. Passing in different arguments will cause the function to
be called again.

Note that this only works if the arguments are hashable!

If you are writing a Zope 3 view, you can do:

 >>> from plone.memoize import view
 >>> class MyView(BrowserView):
 ...   @view.memoize
 ...   def some_expensive_function(self, arg1, arg2):
 ...       return "Some expensive result"

This has the same effect, but subsequent lookup of the same view in the
same context will be memoized as well.

You can also use @view.memoize_contextless to have the memoization not
take the context into account - the same view looked up during the same
request (but possibly on another context) with the same parameters will 
be memoized.

Note that this requires that the request is annotatable using zope.annotation!


generic
=======

The generic decorator uses the GenericCache module as storage. By default
it'll store into a global cache of its own, with default parameters of 1000
maximal objects and 1 hour maximal lifespan.

You can create your own storage area with its specific parameters using
the new_storage method.

Look at the docstring for a few examples.


keys and parameters marshaling
==============================

An important issue about caches is how to generate the cache key. In all
the decorators above, you can create your own function.

The marshallers module provide with useful default marshallers. 
args_marshaller will compute a key from function name, module and
parameters, applying a hash if asked for. Look into the docstring
for usage example.

