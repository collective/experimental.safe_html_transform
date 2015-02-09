"""
Memoize decorator for methods.

Stores values in an annotation of the request.
"""

import inspect

from zope.annotation.interfaces import IAnnotations

from plone.memoize import volatile

_marker = object()


class RequestMemo(object):

    key = 'plone.memoize_request'

    def __init__(self, arg=0):
        self.arg = arg

    def __call__(self, func):

        def memogetter(*args, **kwargs):
            request = None
            if isinstance(self.arg, int):
                request = args[self.arg]
            else:
                request = kwargs[self.arg]

            annotations = IAnnotations(request)
            cache = annotations.get(self.key, _marker)

            if cache is _marker:
                cache = annotations[self.key] = dict()

            key = (func.__module__, func.__name__,
                   args, frozenset(kwargs.items()))
            value = cache.get(key, _marker)
            if value is _marker:
                value = cache[key] = func(*args, **kwargs)
            return value
        return memogetter


def store_in_annotation_of(expr):

    def _store_in_annotation(fun, *args, **kwargs):
        # Use expr to find out the name of the request variable
        vars = {}
        spec = inspect.getargspec(fun)
        num_args = len(args)
        expected_num_args = num_args

        # Explicitly check for the correct number of arguments and
        # raise the appropriate TypeError if needed. This is done
        # to avoid the real problem being masked by an IndexError
        # later in this method.
        if spec[3] is not None:
            expected_num_args = len(spec[0]) - len(spec[3])
        if num_args != expected_num_args:
            raise TypeError("%s() takes exactly %s arguments (%s given)" \
                % (fun.func_name, expected_num_args, num_args))

        for index, name in enumerate(spec[0]):
            if index < num_args:
                vars[name] = args[index]
            else:
                vars[name] = kwargs.get(name, spec[3][index-num_args])
        request = eval(expr, {}, vars)
        return IAnnotations(request)
    return _store_in_annotation


def cache(get_key, get_request='request'):
    r"""
    This is a hypothetical function `increment` that'll store the
    cache value on `a.request`, where a is the only argument to the
    function:

      >>> def increment(a):
      ...     print 'Someone or something called me'
      ...     return a + 1

    Now we need to define this `a`.  For this, we'll inherit from
    `int` and add a `request` class variable.  Note that we also make
    our fake request `IAttributeAnnotatable`, because that's how the
    cache values are stored on the request:

      >>> from zope.publisher.browser import TestRequest
      >>> class A(int):
      ...     request = TestRequest()
      >>> from zope.interface import directlyProvides
      >>> from zope.annotation.interfaces import IAttributeAnnotatable
      >>> directlyProvides(A.request, IAttributeAnnotatable)

    In addition to this request, we'll also need to set up a cache key
    generator.  We'll use the integer value of the only argument for
    that:

      >>> get_key = lambda fun, a, *args: a

    Let's decorate our `increment` function now with the `cache`
    decorator.  We'll tell the decorator to use `args_hash` for
    generating the key. `get_request` will tell the decorator how to
    actually find the `request` in the variable scope of the function
    itself:

      >>> cached_increment = \
      ...     cache(get_key=get_key, get_request='a.request')(increment)

      >>> cached_increment(A(1))
      Someone or something called me
      2
      >>> cached_increment(A(1))
      2
      >>> IAnnotations(A.request)
      {'plone.memoize.request.increment:1': 2}

    If `request` is already part of the function's argument list, we
    don't need to specify any expression:

      >>> @cache(get_key=get_key)
      ... def increment_plus(a, request):
      ...     print 'Someone or something called me'
      ...     return a + 1

      >>> increment_plus(42, A.request)
      Someone or something called me
      43
      >>> increment_plus(42, A.request)
      43
      >>> IAnnotations(A.request)['plone.memoize.request.increment_plus:42']
      43

    Create a function that can also take keyword arguments. For the sake of
    convenience pass the request explicitly. get_key must be modified to take
    kwargs into account:

      >>> def get_key(fun, a, request, **kwargs):
      ...     li = kwargs.items()
      ...     li.sort()
      ...     return "%s,%s" % (a, li)

      >>> @cache(get_key=get_key)
      ... def increment_kwargs(a, request, kwarg1=1, kwarg2=2):
      ...     print 'Someone or something called me'
      ...     return a + 1

      >>> increment_kwargs(42, A.request, kwarg1='kwarg1', kwarg2='kwarg2')
      Someone or something called me
      43
      >>> increment_kwargs(42, A.request, kwarg1='kwarg1', kwarg2='kwarg2')
      43
      >>> IAnnotations(A.request)["plone.memoize.request.increment_kwargs:42,[('kwarg1', 'kwarg1'), ('kwarg2', 'kwarg2')]"]
      43

    Call increment_kwargs without specifying any keyword arguments:

      >>> increment_kwargs(42, A.request)
      Someone or something called me
      43
      >>> increment_kwargs(42, A.request)
      43
      >>> IAnnotations(A.request)["plone.memoize.request.increment_kwargs:42,[]"]
      43

    Call increment_kwargs and specify only the second keyword argument:

      >>> increment_kwargs(42, A.request, kwarg2='kwarg2')
      Someone or something called me
      43
      >>> increment_kwargs(42, A.request, kwarg2='kwarg2')
      43
      >>> IAnnotations(A.request)["plone.memoize.request.increment_kwargs:42,[('kwarg2', 'kwarg2')]"]
      43

    """

    return volatile.cache(get_key,
                          get_cache=store_in_annotation_of(get_request))

memoize_diy_request = RequestMemo

__all__ = (memoize_diy_request, store_in_annotation_of, cache)
