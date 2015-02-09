"""Migration tools for ATContentTypes

Migration system for the migration from CMFDefault/Event types to archetypes
based CMFPloneTypes (http://plone.org/products/atcontenttypes/).

Copyright (c) 2004, Christian Heimes <tiran@cheimes.de> and contributors
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

import sys
import logging
import pkg_resources
from cStringIO import StringIO

from Products.CMFCore.utils import getToolByName
from Products.contentmigration.catalogpatch import applyCatalogPatch
from Products.contentmigration.catalogpatch import removeCatalogPatch


# Is there a multilingual addon?
try:
    pkg_resources.get_distribution('Products.LinguaPlone')
except pkg_resources.DistributionNotFound:
    HAS_LINGUA_PLONE = False
else:
    HAS_LINGUA_PLONE = True

if not HAS_LINGUA_PLONE:
    try:
        pkg_resources.get_distribution('plone.app.multilingual')
    except pkg_resources.DistributionNotFound:
        HAS_LINGUA_PLONE = False
    else:
        HAS_LINGUA_PLONE = True

LOG = logging.getLogger('ATCT.migration')

# This method was coded by me (Tiran) for CMFPlone. I'm maintaining a copy here
# to avoid dependencies on CMFPlone
def _createObjectByType(type_name, container, id, *args, **kw):
    """Create an object without performing security checks

    invokeFactory and fti.constructInstance perform some security checks
    before creating the object. Use this function instead if you need to
    skip these checks.

    This method uses some code from
    CMFCore.TypesTool.FactoryTypeInformation.constructInstance
    to create the object without security checks.

    It doesn't finish the construction and so doesn't reinitializes the workflow.
    """
    id = str(id)
    typesTool = getToolByName(container, 'portal_types')
    fti = typesTool.getTypeInfo(type_name)
    if not fti:
        raise ValueError, 'Invalid type %s' % type_name

    ob = fti._constructInstance(container, id, *args, **kw)

    # in CMF <2.2 the portal type hasn't been set yet
    if 'portal_type' not in ob.__dict__ and hasattr(ob, '_setPortalTypeName'):
        ob._setPortalTypeName(fti.getId())

    return ob

from Acquisition import aq_base
from App.Dialogs import MessageDialog
#from OFS.CopySupport import CopyContainer
from OFS.CopySupport import CopyError
from OFS.CopySupport import eNotSupported
from cgi import escape

def unrestricted_rename(self, id, new_id):
    """Rename a particular sub-object

    Copied from OFS.CopySupport

    Less strict version of manage_renameObject:
        * no write look check
        * no verify object check from PortalFolder so it's allowed to rename
          even unallowed portal types inside a folder
    """
    try: self._checkId(new_id)
    except: raise CopyError, MessageDialog(
                  title='Invalid Id',
                  message=sys.exc_info()[1],
                  action ='manage_main')
    ob=self._getOb(id)
    #!#if ob.wl_isLocked():
    #!#    raise ResourceLockedError, 'Object "%s" is locked via WebDAV' % ob.getId()
    if not ob.cb_isMoveable():
        raise CopyError, eNotSupported % escape(id)
    #!#self._verifyObjectPaste(ob)
    #!#CopyContainer._verifyObjectPaste(self, ob)
    try:    ob._notifyOfCopyTo(self, op=1)
    except: raise CopyError, MessageDialog(
                  title='Rename Error',
                  message=sys.exc_info()[1],
                  action ='manage_main')
    self._delObject(id)
    ob = aq_base(ob)
    ob._setId(new_id)

    # Note - because a rename always keeps the same context, we
    # can just leave the ownership info unchanged.
    self._setObject(new_id, ob, set_owner=0)
    ob = self._getOb(new_id)
    ob._postCopy(self, op=1)

    #!#if REQUEST is not None:
    #!#    return self.manage_main(self, REQUEST, update_menu=1)
    return None

class Registry(dict):
    """Common registry
    """

    def register(self, cls):
        self[cls.__name__] = cls

class MigratorRegistry(Registry):
    """Migrator Registry
    """

    def registerATCT(self, cls, for_cls):
        """Special register method for ATCT based migrators
        """
        cls.src_portal_type = for_cls._atct_newTypeFor['portal_type']
        cls.src_meta_type = for_cls._atct_newTypeFor['meta_type']
        cls.dst_portal_type = for_cls.portal_type
        cls.dst_meta_type = for_cls.meta_type
        self.register(cls)

    def register(self, cls):
        key = (cls.src_meta_type, cls.dst_meta_type)
        assert key not in self
        self[key] = cls
        self[cls.__name__] = cls

class WalkerRegistry(Registry):
    """Walker Registry
    """
    pass

_migratorRegistry = MigratorRegistry()
registerMigrator = _migratorRegistry.register
registerATCTMigrator = _migratorRegistry.registerATCT
listMigrators = _migratorRegistry.items
getMigrator = _migratorRegistry.get

_walkerRegistry = WalkerRegistry()
registerWalker = _walkerRegistry.register
listWalkers = _walkerRegistry.items

def migratePortalType(portal, src_portal_type, dst_portal_type, out=None,
                      migrator=None, use_catalog_patch=False, **kwargs):
    """Migrate from src portal type to dst portal type

    Additional **kwargs are applied to the walker
    """
    if not out:
        out = StringIO()

    # migrators are also registered by (src meta type, dst meta type)
    # let's find the right migrator for us
    ttool = getToolByName(portal, 'portal_types')
    src = ttool.getTypeInfo(src_portal_type)
    dst = ttool.getTypeInfo(dst_portal_type)
    if src is None or dst is None:
        raise ValueError, "Unknown src or dst portal type: %s -> %s" % (
                           src_portal_type, dst_portal_type,)

    key = (src.Metatype(), dst.Metatype())
    migratorFromRegistry = getMigrator(key)
    if migratorFromRegistry is None:
        raise ValueError, "No registered migrator for '%s' found" % str(key)

    if migrator is not None:
        # got a migrator, make sure it is the right one
        if migrator is not migratorFromRegistry:
            raise ValueError, "ups"
    else:
        migrator = migratorFromRegistry

    Walker = migrator.walkerClass

    msg = '--> Migrating %s to %s with %s' % (src_portal_type,
           dst_portal_type, Walker.__name__)
    if use_catalog_patch:
        msg+=', using catalog patch'
    if kwargs.get('use_savepoint', False):
        msg+=', using savepoints'
    if kwargs.get('full_transaction', False):
        msg+=', using full transactions'

    print >> out, msg
    LOG.debug(msg)

    walk = Walker(portal, migrator, src_portal_type=src_portal_type,
                  dst_portal_type=dst_portal_type, **kwargs)
    # wrap catalog patch inside a try/finally clause to make sure that the catalog
    # is unpatched under *any* circumstances (hopely)
    try:
        if use_catalog_patch:
            catalog_class = applyCatalogPatch(portal)
        walk.go()
    finally:
        if use_catalog_patch:
            removeCatalogPatch(catalog_class)

    print >>out, walk.getOutput()
    LOG.debug('<-- Migrating %s to %s done' % (src_portal_type, dst_portal_type))

    return out



