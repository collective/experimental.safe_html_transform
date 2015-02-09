ObjectPath
**********

This package contains two things:

* the ``z3c.objpath.interfaces.IObjectPath`` interface.

* some helper functions to construct (relative) object paths, in
  ``z3c.objpath.path``.

The idea is that a particular application can implement a utility that
fulfills the ``IObjectPath`` interface, so that it is possible to
construct paths to objects in a uniform way. The implementation may be
done with ``zope.traversing``, but in some cases you want
application-specific object paths. In this case, the functions in
``z3c.objpath.path`` might be useful.

We'll have a simple item::

  >>> class Item(object):
  ...   __name__ = None
  ...   __parent__ = None
  ...   def __repr__(self):
  ...     return '<Item %s>' % self.__name__

Let's create a simple container-like object::

  >>> class Container(Item):
  ...   def __init__(self):
  ...     self._d = {}
  ...   def __setitem__(self, name, obj):
  ...     self._d[name] = obj
  ...     obj.__name__ = name
  ...     obj.__parent__ = self
  ...   def __getitem__(self, name):
  ...     return self._d[name]
  ...   def __repr__(self):
  ...     return '<Container %s>' % self.__name__

Now let's create a structure::

  >>> root = Container()
  >>> root.__name__ = 'root'
  >>> data = root['data'] = Container()
  >>> a = data['a'] = Container()
  >>> b = data['b'] = Container()
  >>> c = data['c'] = Item()
  >>> d = a['d'] = Item()
  >>> e = a['e'] = Container()
  >>> f = e['f'] = Item()
  >>> g = b['g'] = Item()

We will now exercise two functions, ``path`` and ``resolve``, which
are inverses of each other::

  >>> from z3c.objpath import path, resolve

We can create a path to ``a`` from ``root``::

  >>> path(root, a)
  '/root/data/a'

We can also resolve it again::

  >>> resolve(root, '/root/data/a')
  <Container a>

We can also create a path to ``a`` from ``data``::

  >>> path(data, a)
  '/data/a'

And resolve it again::

  >>> resolve(data, '/data/a')
  <Container a>

We can make a deeper path::

  >>> path(root, f)
  '/root/data/a/e/f'

And resolve it::

  >>> resolve(root, '/root/data/a/e/f')
  <Item f>

We get an error if we cannot construct a path::

  >>> path(e, a)
  Traceback (most recent call last):
   ...
  ValueError: Cannot create path for <Container a>

We also get an error if we cannot resolve a path::

  >>> resolve(root, '/root/data/a/f/e')
  Traceback (most recent call last):
   ...
  ValueError: Cannot resolve path /root/data/a/f/e
