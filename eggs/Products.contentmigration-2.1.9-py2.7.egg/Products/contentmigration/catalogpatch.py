"""Migration tools for ATContentTypes

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

# Catalog patches for ATCT migration
#
# The catalog patches are patching catalog_object and uncatalog_object in order to
# speed up the migration. Especially for folder migration with hundreds or more
# children the speed gain can be immense.
#
# The patch is altering uncatalog_object to do nothing so that objects aren't
# uncataloged. catalog_object is altered to update only a small subset of the
# indexes and no metadata. Only indexes that are used in the migration are updated.
#
# applyCatalogPatch and removeCatalogPatch must be wrapped in a try/finally block!
#
# indexObject(), unindexObject() and reindexObject() are using catalog_object() and
# uncatalog_object(). There is no need to patch these methods.

import logging
# instancemethod(function, instance, class)
# Create an instance method object.
from types import MethodType as instancemethod

from Products.CMFCore.utils import getToolByName

LOG = logging.getLogger('ATCT.migration')
UPDATE_METADATA = False
IDXS = ('meta_type', 'portal_type', 'path')

def uncatalog_object(self, uid):
    """NOOP uncatalog_object
    """
    pass

def catalog_object(self, obj, uid=None, idxs=None, update_metadata=1,
                   pghandler=None):
   """Minimalistic catalog_object method
   """
   return self._atct_catalog_object(obj, uid=uid, idxs=IDXS,
                                    update_metadata=UPDATE_METADATA,
                                    pghandler=None)

def applyCatalogPatch(portal):
    """Patch catalog
    """
    catalog = getToolByName(portal, 'portal_catalog')
    klass = catalog.__class__
    LOG.info('Patching catalog_object and uncatalog_object of %s' %
             catalog.absolute_url(1))
    if hasattr(klass, '_atct_catalog_object'):
        raise RuntimeError, "%s already has _atct_catalog_object" % catalog
    if hasattr(klass, '_atct_uncatalog_object'):
        raise RuntimeError, "%s already has _atct_uncatalog_object" % catalog

    klass._atct_catalog_object = klass.catalog_object.im_func
    klass.catalog_object = instancemethod(catalog_object, None, klass)

    klass._atct_uncatalog_object = klass.uncatalog_object.im_func
    klass.uncatalog_object = instancemethod(uncatalog_object, None, klass)

    return klass

def removeCatalogPatch(klass):
    """Unpatch catalog

    removeCatalogPatch must be called with the catalog class and not with the portal
    as argument. If migration fails the transaction is aborted explictly. The portal
    doesn't exist any longer and the method would be unable to acquire the
    portal_catalog.
    """
    LOG.info('Unpatching catalog_object and uncatalog_object')

    if hasattr(klass, '_atct_catalog_object'):
        klass.catalog_object = klass._atct_catalog_object.im_func
        del klass._atct_catalog_object

    if hasattr(klass, '_atct_uncatalog_object'):
        klass.uncatalog_object = klass._atct_uncatalog_object.im_func
        del klass._atct_uncatalog_object
