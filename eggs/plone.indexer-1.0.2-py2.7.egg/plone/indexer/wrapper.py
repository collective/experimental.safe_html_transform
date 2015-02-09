from zope.interface import implements
from zope.interface import providedBy
from zope.interface import Interface
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor

from zope.component import adapts
from zope.component import queryMultiAdapter

from plone.indexer.interfaces import IIndexableObjectWrapper
from plone.indexer.interfaces import IIndexableObject
from plone.indexer.interfaces import IIndexer

from Products.ZCatalog.interfaces import IZCatalog
from Products.CMFCore.utils import getToolByName


class WrapperSpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the wrapped object when asked.
    """

    def __get__(self, inst, cls=None):
        if inst is None:
            return getObjectSpecification(cls)
        else:
            provided = providedBy(inst._IndexableObjectWrapper__object)
            cls = type(inst)
            return ObjectSpecification(provided, cls)


class IndexableObjectWrapper(object):
    """A simple wrapper for indexable objects that will delegate to IIndexer
    adapters as appropriate.
    """

    implements(IIndexableObject, IIndexableObjectWrapper)
    adapts(Interface, IZCatalog)

    __providedBy__ = WrapperSpecification()

    def __init__(self, object, catalog):
        self.__object = object
        self.__catalog = catalog
        self.__vars = {}

        portal_workflow = getToolByName(catalog, 'portal_workflow', None)
        if portal_workflow is not None:
            self.__vars = portal_workflow.getCatalogVariablesFor(object)

    def _getWrappedObject(self):
        return self.__object

    def __str__(self):
        try:
            return self.__object.__str__()
        except AttributeError:
            return object.__str__(self)

    def __getattr__(self, name):
        # First, try to look up an indexer adapter
        indexer = queryMultiAdapter((self.__object, self.__catalog), IIndexer, name=name)
        if indexer is not None:
            return indexer()

        # Then, try workflow variables
        if name in self.__vars:
            return self.__vars[name]

        # Finally see if the object provides the attribute directly. This
        # is allowed to raise AttributeError.
        return getattr(self.__object, name)
