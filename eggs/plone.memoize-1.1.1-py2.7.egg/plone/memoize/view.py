"""
Memoize decorator for views.

Stores values in an annotation of the request. See view.txt.
"""

from zope.annotation.interfaces import IAnnotations

_marker = object()


class ViewMemo(object):

    key = 'plone.memoize'

    def memoize(self, func):

        def memogetter(*args, **kwargs):
            instance = args[0]

            context = getattr(instance, 'context', None)
            request = getattr(instance, 'request', None)

            annotations = IAnnotations(request)
            cache = annotations.get(self.key, _marker)

            if cache is _marker:
                cache = annotations[self.key] = dict()

            # XXX: Not the most elegant thing in the world; in a Zope 2
            # context, the physical path is a better key, since the id could
            # change if the object is invalidated from the ZODB cache

            try:
                context_id = context.getPhysicalPath()
            except AttributeError:
                context_id = id(context)

            # Note: we don't use args[0] in the cache key, since args[0] ==
            # instance and the whole point is that we can cache different
            # requests

            key = (context_id, instance.__class__.__name__, func.__name__,
                   args[1:], frozenset(kwargs.items()))
            value = cache.get(key, _marker)
            if value is _marker:
                value = cache[key] = func(*args, **kwargs)
            return value
        return memogetter

    def memoize_contextless(self, func):

        def memogetter(*args, **kwargs):
            instance = args[0]
            request = getattr(instance, 'request', None)

            annotations = IAnnotations(request)
            cache = annotations.get(self.key, _marker)

            if cache is _marker:
                cache = annotations[self.key] = dict()

            key = (instance.__class__.__name__, func.__name__,
                   args[1:], frozenset(kwargs.items()))
            value = cache.get(key, _marker)
            if value is _marker:
                value = cache[key] = func(*args, **kwargs)
            return value
        return memogetter

_m = ViewMemo()
memoize = _m.memoize
memoize_contextless = _m.memoize_contextless

__all__ = (memoize, memoize_contextless)
