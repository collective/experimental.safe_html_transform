"""This module defines a decorator that
"""

from zope.component import adapter
from plone.indexer.delegate import DelegatingIndexerFactory
from Products.ZCatalog.interfaces import IZCatalog


class indexer(adapter):
    """The @indexer decorator can be used like this:

        >>> from plone.indexer.decorator import indexer
        >>> @indexer(IMyType)
        ... def some_attribute(object):
        ...     return "some indexable value"

    Note that the @indexer decorator is a superset of the @adapter decorator
    from zope.component.

    To register an indexer for a special type of catalog, use:

        >>> from plone.indexer.decorator import indexer
        >>> @indexer(IMyType, IMyCatalog)
        ... def some_attribute(object):
        ...     return "some indexable value"

    The default is to register the indexer for all IZCatalog catalogs.

    Once you've created an indexer, you can register the adapter in ZCML:

        <adapter factory=".myindexers.some_attribute" name="some_attribute" />

    At this point, the indexable object wrapper will ensure that when
    some_attribute is indexed on an object providing IMyType
    """

    def __init__(self, *interfaces):
        if len(interfaces) == 1:
            interfaces += (IZCatalog, )
        elif len(interfaces) > 2:
            raise ValueError(u"The @indexer decorator takes at most two interfaces as arguments")
        adapter.__init__(self, *interfaces)

    def __call__(self, callable):
        factory = DelegatingIndexerFactory(callable)
        return adapter.__call__(self, factory)
