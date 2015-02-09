import logging

from Products.ZCatalog.Catalog import mergeResults

from Products.contentmigration.common import HAS_LINGUA_PLONE
from Products.contentmigration.basemigrator.walker import CatalogWalker, registerWalker

LOG = logging.getLogger('contentmigration')


class CustomQueryWalker(CatalogWalker):
    """Walker using portal_catalog and an optional custom query. The ATCT
    migration framework uses this to find content to migrate.
    """
    additionalQuery = {}

    def __init__(self, portal, migrator, src_portal_type=None, dst_portal_type=None,
                    query={}, callBefore=None, **kwargs):
        """Set up the walker. See contentmigration.basemigrator.walker for details.

        The 'query' parameter can be used to pass a dict with custom catalog
        query parameters. Note that portal_type and meta_type will be set
        based on src_portal_type or, if given, the src_portal_type in the
        migrator.

        The 'callBefore' parameter can be used to pass a function that will
        be called before each item is migrated. If it returns False, the item
        will be skipped. It should have the signature:

            callBefore(oldObject, **kwargs)

        The kwargs passed to this constructor will be passed along to the
        test function.
        """
        CatalogWalker.__init__(self, portal, migrator,
                               src_portal_type=src_portal_type,
                               dst_portal_type=dst_portal_type, **kwargs)
        self.additionalQuery.update(query)
        self.callBefore = callBefore
        self.kwargs = kwargs


    def walk(self):
        """Walks around and returns all objects which needs migration

        :return: objects (with acquisition wrapper) that needs migration
        :rtype: generator
        """
        catalog = self.catalog
        query = self.additionalQuery.copy()
        query['portal_type'] = self.src_portal_type
        query['meta_type'] = self.src_meta_type

        if HAS_LINGUA_PLONE and 'Language' in catalog.indexes():
            query['Language'] = 'all'

        brains = catalog(query)
        limit = getattr(self, 'limit', False)
        if limit:
            brains = brains[:limit]

        for brain in brains:
            try:
                obj = brain.getObject()
            except AttributeError:
                LOG.error("Couldn't access %s" % brain.getPath())
                continue

            if self.callBefore is not None and callable(self.callBefore):
                if self.callBefore(obj, **self.kwargs) == False:
                    continue

            try:
                state = obj._p_changed
            except:
                state = 0
            if obj is not None:
                yield obj
                # safe my butt
                if state is None:
                    obj._p_deactivate()

registerWalker(CustomQueryWalker)

class MultiCustomQueryWalker(CustomQueryWalker):
    """A catalog walker that combines the results from multiple
    queries."""

    additionalQueries = ()

    def walk(self):
        """Walks around and returns all objects which needs migration

        :return: objects (with acquisition wrapper) that needs migration
        :rtype: generator
        """
        catalog = self.catalog
        query = self.additionalQuery
        query['portal_type'] = self.src_portal_type
        query['meta_type'] = self.src_meta_type

        if HAS_LINGUA_PLONE and 'Language' in catalog.indexes():
            #query['Language'] = catalog.uniqueValuesFor('Language')
            query['Language'] = 'all'

        results = []
        for addQ in self.additionalQueries:
            addQ.update(query)
            results.append(catalog(addQ))
        brains = mergeResults(results, has_sort_keys=False,
                              reverse=False)

        for brain in brains:
            obj = brain.getObject()

            if self.callBefore is not None and callable(self.callBefore):
                if self.callBefore(obj, **self.kwargs) == False:
                    continue

            try: state = obj._p_changed
            except: state = 0
            if obj is not None:
                yield obj
                # safe my butt
                if state is None: obj._p_deactivate()

registerWalker(MultiCustomQueryWalker)
