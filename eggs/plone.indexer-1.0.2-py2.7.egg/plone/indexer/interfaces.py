from zope.interface import Interface

# NOTE: CMF 2.2 provides standard interfaces for indexing. We provide
# compatibility aliases here for CMF 2.1

try:
    from Products.CMFCore.interfaces import IIndexableObjectWrapper
except ImportError:
    class IIndexableObjectWrapper(Interface):
        pass
try:
    from Products.CMFCore.interfaces import IIndexableObject
except ImportError:
    class IIndexableObject(Interface):
        """An object being indexed in the catalog. The indexable object
        wrapper will be looked up as a multi-adapter of (object, catalog)
        to this interface if the object being indexed in the catalog does
        not already provide this interface.
        """


class IIndexer(Interface):
    """A component that can provide the value for an catalog index.

    Register a named adapter from an indexable object type (e.g. a content
    object) and the catalog to this interface.

    The name of the adapter should be the same as the name of the indexable
    attribute in the catalog.

    See also decorator.py, for a simpler indexer based on a function
    decorator.
    """

    def __call__(self):
        """Return the value to index.
        """


class IDelegatingIndexableObjectWrapper(IIndexableObjectWrapper):
    """An adapter of a (object, catalog) where object is to be indexed in
    the catalog and catalog is the portal_catalog or similar ZCatalog instance.

    The catalog will call getattr() on the wrapper for each attribute to be
    indexed. The wrapper may either implement these directly (as methods
    taking no parameters) or implement __getattr__() appropriately.
    """

    def _getWrappedObject():
        """Return the object that was wrapped.

        This has a leading underscore to reduce the risk of clashing with
        an index or metadata column.
        """
