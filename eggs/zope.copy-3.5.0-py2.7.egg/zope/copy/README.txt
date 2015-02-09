==============
Object copying
==============

This package provides a pluggable way to copy persistent objects. It
was once extracted from the zc.copy package to contain much less
dependencies. In fact, we only depend on zope.interface to provide
pluggability.

The package provides a ``clone`` function that does the object cloning
and the ``copy`` wrapper that sets __parent__ and __name__ attributes
of object's copy to None. This is useful, when working with Zope's
located objects (see zope.location package). The ``copy`` function
actually calls the ``clone`` function so we'll use the first one in
the examples below. We'll also look a bit at their differences in the
end of this document. 

The ``clone`` function (and thus the ``copy`` function that wraps it)
uses pickling to copy the object and all its subobjects recursively.
As each object and subobject is pickled, the function tries to adapt it
to ``zope.copy.interfaces.ICopyHook``. If a copy hook is found,
the recursive copy is halted.  The hook is called with two values: the
main, top-level object that is being copied; and a callable that supports
registering functions to be called after the copy is made. The copy hook
should return the exact object or subobject that should be used at this
point in the copy, or raise ``zope.copy.interfaces.ResumeCopy``
exception to resume copying the object or subobject recursively after
all.

Note that we use zope's component architecture provided by the
``zope.component`` package in this document, but the
``zope.copy`` package itself doesn't use or depend on it, so
you can provide another adaptation mechanism as described in zope.interface's
adapter documentation.

Simple hooks
------------

First let's examine a simple use. A hook is to support the use case of
resetting the state of data that should be changed in a copy -- for
instance, a log, or freezing or versioning data. The canonical way to
do this is by storing the changable data on a special sub-object of the
object that is to be copied. We'll look at a simple case of a subobject
that should be converted to None when it is copied -- the way that the
zc.freeze copier hook works. Also see the zc.objectlog copier module
for a similar example.

So, here is a simple object that stores a boolean on a special object.

    >>> class Demo(object):
    ...     _frozen = None
    ...     def isFrozen(self):
    ...         return self._frozen is not None
    ...     def freeze(self):
    ...         self._frozen = Data()
    ...
    >>> class Data(object):
    ...     pass
    ...

Here's what happens if we copy one of these objects without a copy hook.

    >>> original = Demo()
    >>> original.isFrozen()
    False
    >>> original.freeze()
    >>> original.isFrozen()
    True
    >>> import zope.copy
    >>> copy = zope.copy.copy(original)
    >>> copy is original
    False
    >>> copy.isFrozen()
    True

Now let's make a super-simple copy hook that always returns None, no
matter what the top-level object being copied is.  We'll register it and
make another copy.

    >>> import zope.component
    >>> import zope.interface
    >>> import zope.copy.interfaces
    >>> def _factory(obj, register):
    ...     return None
    >>> @zope.component.adapter(Data)
    ... @zope.interface.implementer(zope.copy.interfaces.ICopyHook)
    ... def data_copyfactory(obj):
    ...     return _factory
    ...

    >>> zope.component.provideAdapter(data_copyfactory)
    >>> copy2 = zope.copy.copy(original)
    >>> copy2 is original
    False
    >>> copy2.isFrozen()
    False

Much better.

Post-copy functions
-------------------

Now, let's look at the registration function that the hook can use.  It
is useful for resetting objects within the new copy -- for instance, back
references such as __parent__ pointers.  This is used concretely in the
zc.objectlog.copier module; we will come up with a similar but artificial
example here.

Imagine an object with a subobject that is "located" (i.e., zope.location) on
the parent and should be replaced whenever the main object is copied.

    >>> import zope.location.location
    >>> class Subobject(zope.location.location.Location):
    ...     def __init__(self):
    ...         self.counter = 0
    ...     def __call__(self):
    ...         res = self.counter
    ...         self.counter += 1
    ...         return res
    ...
    >>> o = zope.location.location.Location()
    >>> s = Subobject()
    >>> o.subobject = s
    >>> zope.location.location.locate(s, o, 'subobject')
    >>> s.__parent__ is o
    True
    >>> o.subobject()
    0
    >>> o.subobject()
    1
    >>> o.subobject()
    2

Without an ICopyHook, this will simply duplicate the subobject, with correct
new pointers.

    >>> c = zope.copy.copy(o)
    >>> c.subobject.__parent__ is c
    True

Note that the subobject has also copied state.

    >>> c.subobject()
    3
    >>> o.subobject()
    3

Our goal will be to make the counters restart when they are copied.  We'll do
that with a copy hook.

This copy hook is different: it provides an object to replace the old object,
but then it needs to set it up further after the copy is made.  This is
accomplished by registering a callable, ``reparent`` here, that sets up the
__parent__.  The callable is passed a function that can translate something
from the original object into the equivalent on the new object.  We use this
to find the new parent, so we can set it.

    >>> import zope.component
    >>> import zope.interface
    >>> import zope.copy.interfaces
    >>> @zope.component.adapter(Subobject)
    ... @zope.interface.implementer(zope.copy.interfaces.ICopyHook)
    ... def subobject_copyfactory(original):
    ...     def factory(obj, register):
    ...         obj = Subobject()
    ...         def reparent(translate):
    ...             obj.__parent__ = translate(original.__parent__)
    ...         register(reparent)
    ...         return obj
    ...     return factory
    ...
    >>> zope.component.provideAdapter(subobject_copyfactory)

Now when we copy, the new subobject will have the correct, revised __parent__,
but will be otherwise reset (here, just the counter)

    >>> c = zope.copy.copy(o)
    >>> c.subobject.__parent__ is c
    True
    >>> c.subobject()
    0
    >>> o.subobject()
    4

Resuming recursive copy
-----------------------

One thing we didn't examine yet is the use of ResumeCopy exception in
the copy hooks. For example, when copying located objects we don't want
to copy referenced subobjects that are not located in the object that
is being copied. Imagine, we have a content object that has an image object,
referenced by the ``cover`` attribute, but located in an independent
place.

    >>> root = zope.location.location.Location()

    >>> content = zope.location.location.Location()
    >>> zope.location.location.locate(content, root, 'content')

    >>> image = zope.location.location.Location()
    >>> zope.location.location.locate(image, root, 'image.jpg')

    >>> content.cover = image
  
Without any hooks, the image object will be cloned as well:

    >>> new = zope.copy.copy(content)
    >>> new.cover is image
    False

That's not what we'd expect though, so, let's provide a copy hook
to deal with that. The copy hook for this case is provided by zope.location
package, but we'll create one from scratch as we want to check out the
usage of the ResumeCopy. 

    >>> @zope.component.adapter(zope.location.interfaces.ILocation)
    ... @zope.interface.implementer(zope.copy.interfaces.ICopyHook)
    ... def location_copyfactory(obj):
    ...     def factory(location, register):
    ...         if not zope.location.location.inside(obj, location):
    ...             return obj
    ...         raise zope.copy.interfaces.ResumeCopy
    ...     return factory
    ...
    >>> zope.component.provideAdapter(location_copyfactory)

This hook returns objects as they are if they are not located inside
object that's being copied, or raises ResumeCopy to signal that the
recursive copy should be continued and used for the object.

    >>> new = zope.copy.copy(content)
    >>> new.cover is image
    True

Much better :-)

``clone`` vs ``copy``
---------------------

As we stated before, there's two functions that is used for copying
objects. The ``clone`` - that does the job, and its wrapper, ``copy``
that calls ``clone`` and then clears copy's __parent__ and __name__
attribute values.

Let's create a location object with __name__ and __parent__ set.

    >>> root = zope.location.location.Location()
    >>> folder = zope.location.location.Location()
    >>> folder.__name__ = 'files'
    >>> folder.__parent__ = root

The ``clone`` function will leave those attributes as is. Note that the
referenced __parent__ won't be cloned, as we registered a hook for locations
in the previous section.

    >>> folder_clone = zope.copy.clone(folder)
    >>> folder_clone.__parent__ is root
    True
    >>> folder_clone.__name__ == 'files'
    True

However, the ``copy`` function will reset those attributes to None, as
we will probably want to place our object into another container with
another name.

    >>> folder_clone = zope.copy.copy(folder)
    >>> folder_clone.__parent__ is None
    True
    >>> folder_clone.__name__ is None
    True

Notice, that if your object doesn't have __parent__ and __name__
attributes at all, or these attributes could'nt be got or set because of
some protections (as with zope.security's proxies, for example), you still
can use the ``copy`` function, because it works for objects that don't
have those attributes.

It won't set them if original object doesn't have them:

    >>> class Something(object):
    ...     pass

    >>> s = Something()
    >>> s_copy = zope.copy.copy(s)
    >>> s_copy.__parent__
    Traceback (most recent call last):
    ...
    AttributeError: ...
    >>> s_copy.__name__
    Traceback (most recent call last):
    ...
    AttributeError: ...

And it won't fail if original object has them but doesn't allow to set
them.

    >>> root = object()
    >>> class Something(object):
    ...
    ...     @apply
    ...     def __name__():
    ...         def fget(self):
    ...             return 'something'
    ...         def fset(self, value):
    ...             raise AttributeError
    ...         return property(fget, fset)
    ...
    ...     @apply
    ...     def __parent__():
    ...         def fget(self):
    ...             return root
    ...         def fset(self, value):
    ...             raise AttributeError
    ...         return property(fget, fset)

    >>> s = Something()
    >>> s_copy = zope.copy.copy(s)
    >>> s_copy.__parent__ is root
    True
    >>> s_copy.__name__ == 'something'
    True
