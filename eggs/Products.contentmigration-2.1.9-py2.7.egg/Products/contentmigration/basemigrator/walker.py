"""Walkers for Migration suite

Migration system for the migration from CMFDefault/Event types to archetypes
based CMFPloneTypes (http://plone.org/products/atcontenttypes/).

Copyright (c) 2004-2005, Christian Heimes <tiran@cheimes.de> and contributors
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
 * Neither the name of the author nor the names of its contributors may be used
   to endorse or promote products derived from this software without specific
   prior written permission.
"""
__author__  = 'Christian Heimes <tiran@cheimes.de>'
__docformat__ = 'restructuredtext'

import logging
import traceback
import transaction
from cStringIO import StringIO

from Products.contentmigration.common import HAS_LINGUA_PLONE
from Products.contentmigration.common import registerWalker
from ZODB.POSException import ConflictError
from Products.CMFCore.utils import getToolByName

LOG = logging.getLogger('ATCT.migration')

# archetypes.schemaextender addon?
try:
    # beware of moving this, the top-level package has an archetypes module
    from archetypes.schemaextender.extender import disableCache
    disableCache
except ImportError:
    def disableCache(request):
        pass


class StopWalking(StopIteration):
    pass


class MigrationError(RuntimeError):
    def __init__(self, path, migrator, traceback):
        self.src_portal_type = migrator.src_portal_type
        self.dst_portal_type = migrator.dst_portal_type
        self.tb = traceback
        self.path = path

    def __str__(self):
        return "MigrationError for obj at %s (%s -> %s):\n%s" % (self.path,
                    self.src_portal_type, self.dst_portal_type, self.tb)

class Walker(object):
    """Walks through the system and migrates every object it finds

    arguments:
    * portal
      portal root object as context
    * migrator
      migrator class
    * src and dst_portal_type
      ids of the portal types to migrate
    * transaction_size (int)
      Amount of objects before a transaction, subtransaction or new savepoint is
      created. A small number might slow down the process since transactions are
      possible costly.
    * full_transaction
      Commit a full transaction after transaction size
    * use_savepoint
      Create savepoints and roll back to the savepoint if an error occurs
    * limit
      Limits the catalog query to at most x items

    full_transaction and use_savepoint are mutual exclusive.
    o When the default values (both False) are used a subtransaction is committed.
      If an error occurs *all* changes are lost.
    o If full_transaction is enabled a full transaction is committed. If an error
      occurs the migration process stops and all changes sine the last transaction
      are lost.
    o If use_savepoint is set savepoints are used. A savepoint is like a
      subtransaction which can be rolled back. If an errors occurs the transaction
      is rolled back to the last savepoint and the migration goes on. Some objects
      will be left unmigrated.

    """

    def __init__(self, portal, migrator, src_portal_type=None, dst_portal_type=None,
                 **kwargs):
        self.portal = portal
        self.catalog = getToolByName(portal, 'portal_catalog')
        self.migrator = migrator
        if src_portal_type is None:
            self.src_portal_type = self.migrator.src_portal_type
        else:
            self.src_portal_type = src_portal_type
        if dst_portal_type is None:
            self.dst_portal_type = self.migrator.dst_portal_type
        else:
            self.dst_portal_type = dst_portal_type
        self.src_meta_type = self.migrator.src_meta_type
        self.dst_meta_type = self.migrator.dst_meta_type

        self.transaction_size = int(kwargs.get('transaction_size', 20))
        self.full_transaction = kwargs.get('full_transaction', False)
        self.use_savepoint = kwargs.get('use_savepoint', False)
        self.limit = kwargs.get('limit', False)

        if self.full_transaction and self.use_savepoint:
            raise ValueError

        self.out = StringIO()
        self.counter = 0
        self.errors = []

        # Disable schema cache
        request = getattr(portal, 'REQUEST', None)
        if request is not None:
            disableCache(request)

    def go(self, **kwargs):
        """runner

        Call it to start the migration
        """
        # catalog subtransaction conflict w/ savepoints because a subtransaction
        # destroys all existing savepoints.
        # disable subtransactions for all known catalogs and restore them later
        old_thresholds = {}
        for id in ('portal_catalog', 'uid_catalog', 'reference_catalog'):
            catalog = getToolByName(self.portal, id, None)
            if catalog is not None:
                old_thresholds[id] = getattr(self.catalog, 'threshold', None)
                catalog.threshold = None

        try:
            self.migrate(self.walk(), **kwargs)
        finally:
            for id, threshold in old_thresholds.items():
                catalog = getToolByName(self.portal, id, None)
                if catalog is not None:
                    catalog.threshold = threshold

    __call__ = go

    def walk(self):
        """Walks around and returns all objects which needs migration

        :return: objects (with acquisition wrapper) that needs migration
        :rtype: list of objects
        """
        raise NotImplementedError

    def migrate(self, objs, **kwargs):
        """Migrates the objects in the ist objs
        """
        out = self.out
        counter = self.counter
        errors = self.errors
        full_transaction = self.full_transaction
        transaction_size = self.transaction_size
        use_savepoint = self.use_savepoint

        src_portal_type = self.src_portal_type
        dst_portal_type = self.dst_portal_type

        if use_savepoint:
            savepoint = transaction.savepoint()

        for obj in objs:
            objpath = '/'.join(obj.getPhysicalPath())
            msg = 'Migrating %s (%s -> %s)' % (objpath, src_portal_type,
                                               dst_portal_type)
            LOG.debug(msg)
            print >>out, msg
            counter+=1

            migrator = self.migrator(obj,
                                     src_portal_type=src_portal_type,
                                     dst_portal_type=dst_portal_type,
                                     **kwargs)

            try:
                # run the migration
                migrator.migrate()
            except ConflictError:
                raise
            except: # except all!
                msg = "Failed migration for object %s (%s -> %s)" %  (objpath,
                           src_portal_type, dst_portal_type)
                # printing exception
                f = StringIO()
                traceback.print_exc(limit=None, file=f)
                tb = f.getvalue()

                LOG.error(msg, exc_info = True)
                errors.append({'msg' : msg, 'tb' : tb, 'counter': counter})

                if use_savepoint:
                    if savepoint.valid:
                        # Rollback to savepoint
                        LOG.info("Rolling back to last safe point")
                        print >>out, msg
                        print >>out, tb
                        savepoint.rollback()
                        # XXX: savepoints are invalidated once they are used
                        savepoint = transaction.savepoint()
                        continue
                    else:
                        LOG.error("Savepoint is invalid. Probably a subtransaction "
                            "was committed. Unable to roll back!")
                #  stop migration process after an error
                # aborting transaction
                LOG.error("FATAL: Migration has failed, aborting transaction!")
                transaction.abort()
                raise MigrationError(objpath, migrator, tb)

            if counter % transaction_size == 0:
                if full_transaction:
                    transaction.commit()
                    LOG.debug('Transaction comitted after %s objects' % counter)
                elif use_savepoint:
                    LOG.debug('Creating new safepoint after %s objects' % counter)
                    savepoint = transaction.savepoint()
                else:
                    LOG.debug('Committing subtransaction after %s objects' % counter)
                    transaction.savepoint(optimistic=True)

        self.out = out
        self.counter = counter
        self.errors = errors

    def getOutput(self):
        """Get migration notes

        :return: objects (with acquisition wrapper) that needs migration
        :rtype: list of objects
        """
        return self.out.getvalue()

class CatalogWalker(Walker):
    """Walker using portal_catalog
    """

    def walk(self):
        """Walks around and returns all objects which needs migration

        :return: objects (with acquisition wrapper) that needs migration
        :rtype: generator
        """
        catalog = self.catalog
        query = {
            'portal_type' : self.src_portal_type,
            'meta_type' : self.src_meta_type,
            'path' : "/".join(self.portal.getPhysicalPath()),
        }
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
            try:
                state = obj._p_changed
            except:
                state = 0
            if obj is not None:
                yield obj
                # safe my butt
                if state is None:
                    obj._p_deactivate()

registerWalker(CatalogWalker)

class CatalogWalkerWithLevel(Walker):
    """Walker using the catalog but only returning objects for a specific depth

    Requires ExtendedPathIndex!
    """

    def __init__(self, portal, migrator, src_portal_type=None, dst_portal_type=None,
                 depth=1, max_depth=100, **kwargs):
        Walker.__init__(self, portal, migrator, src_portal_type, dst_portal_type,
                        **kwargs)
        self.depth=depth
        self.max_depth = max_depth

    def walk(self):
        """Walks around and returns all objects which needs migration

        :return: objects (with acquisition wrapper) that needs migration
        :rtype: generator

        TODO: stop when no objects are left. Don't try to migrate until the walker
              reaches max_depth
        """
        depth = self.depth
        max_depth = self.max_depth
        catalog = self.catalog
        root = '/'.join(self.portal.getPhysicalPath())
        rootlen = len(root)
        query = {
            'portal_type' : self.src_portal_type,
            'meta_type' : self.src_meta_type,
            'path' : {'query' : root, 'depth' : depth},
        }

        if HAS_LINGUA_PLONE and 'Language' in catalog.indexes():
            #query['Language'] = catalog.uniqueValuesFor('Language')
            query['Language'] = 'all'

        while True:
            if depth > max_depth:
                raise StopWalking
            query['path']['depth'] = depth
            for brain in catalog(query):
                # depth 'n' returns objects with depth of 'n' and *smaller*
                # but we want to migrate only object with a depth of
                # exactly 'n'
                relpath = brain.getPath()[rootlen:]
                if not relpath.count('/') == depth:
                    continue

                obj = brain.getObject()
                try: state = obj._p_changed
                except: state = 0
                if obj is not None:
                    yield obj
                    # safe my butt
                    if state is None: obj._p_deactivate()

            depth+=1

registerWalker(CatalogWalkerWithLevel)

def useLevelWalker(portal, migrator, **kwargs):
    w = CatalogWalkerWithLevel(portal, migrator)
    return w.go(**kwargs)
