from zope.interface import implements
from zope.interface.declarations import Implements, implementedBy
from plone.indexer.interfaces import IIndexer
from functools import update_wrapper


class DelegatingIndexer(object):
    """An indexer that delegates to a given callable
    """
    implements(IIndexer)

    def __init__(self, context, catalog, callable):
        self.context = context
        self.catalog = catalog
        self.callable = callable

    def __call__(self):
        return self.callable(self.context)


class DelegatingIndexerFactory(object):
    """An adapter factory for an IIndexer that works by calling a
    DelegatingIndexer.
    """

    def __init__(self, callable):
        self.callable = callable
        self.__implemented__ = Implements(implementedBy(DelegatingIndexer))
        update_wrapper(self, callable)

    def __call__(self, object, catalog=None):
        return DelegatingIndexer(object, catalog, self.callable)
