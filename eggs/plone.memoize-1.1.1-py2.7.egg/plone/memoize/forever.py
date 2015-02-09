"""
Memo decorators for globals - memoized values survive for as long as the
process lives.

Stores values in a module-level variable.

Pay attention that is module is not thread-safe, so use it with care.
"""

from plone.memoize import volatile

_memos = {}


def memoize(fun):

    def get_key(fun, *args, **kwargs):
        return (args, frozenset(kwargs.items()), )

    def get_cache(fun, *args, **kwargs):
        return _memos

    return volatile.cache(get_key, get_cache)(fun)

__all__ = (memoize, )
