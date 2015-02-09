"""
Memoize decorator for methods whose first argument is the request.

Stores values in an annotation of the request.

This is based on ViewMemo from plone.memoize.
"""

from zope.annotation.interfaces import IAnnotations

_marker = object()
class PTSMemo(object):

    key = 'pts.memoize'

    def memoize(self, func):
        def memogetter(*args, **kwargs):
            instance = args[0]
            request = args[1]

            annotations = IAnnotations(request)
            cache = annotations.get(self.key, _marker)

            if cache is _marker:
                cache = annotations[self.key] = dict()

            key = hash((instance.__class__.__name__, func.__name__,
                        args[1:], frozenset(kwargs.items())),)
            value = cache.get(key, _marker)
            if value is _marker:
                value = cache[key] = func(*args, **kwargs)
            return value
        return memogetter

_m = PTSMemo()
memoize = _m.memoize

class NegotiatorMemo(object):

    key = 'pts.memoize_second'

    def memoize(self, func):
        def memogetter(*args):
            instance = args[0]
            langs = args[1]
            request = args[2]

            annotations = IAnnotations(request, None)
            if annotations is None:
                return func(*args)

            cache = annotations.get(self.key, _marker)
            if cache is _marker:
                cache = annotations[self.key] = dict()

            key = hash((instance.__class__.__name__, func.__name__, tuple(langs)),)
            value = cache.get(key, _marker)
            if value is _marker:
                value = cache[key] = func(*args)
            return value
        return memogetter

_n = NegotiatorMemo()
memoize_second = _n.memoize

__all__ = (memoize, memoize_second, )
