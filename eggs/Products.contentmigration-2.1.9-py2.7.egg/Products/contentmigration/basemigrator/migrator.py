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
__author__ = 'Christian Heimes <tiran@cheimes.de>'
__docformat__ = 'restructuredtext'

from copy import copy
import logging

from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from DateTime import DateTime
from Persistence import PersistentMapping
from zope.component import queryAdapter
from zope.component import queryUtility
from OFS.Uninstalled import BrokenClass
from OFS.interfaces import IOrderedContainer
from ZODB.POSException import ConflictError
from zExceptions import BadRequest
from AccessControl.Permission import Permission
from AccessControl import SpecialUsers
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCatalogAware import WorkflowAware
from Products.contentmigration.common import unrestricted_rename
from Products.contentmigration.common import _createObjectByType
from Products.contentmigration.utils import patch, undoPatch
from Products.Archetypes.interfaces import IReferenceable
from plone.locking.interfaces import ILockable
from plone.uuid.interfaces import IMutableUUID
try:
    from plone.app.redirector.interfaces import IRedirectionStorage
    IRedirectionStorage  # pyflakes
except ImportError:
    IRedirectionStorage = None
try:
    from Products.Archetypes.config import UUID_ATTR
except ImportError:
    UUID_ATTR = None

LOG = logging.getLogger('ATCT.migration')

_marker = []

# Dublin Core mapping
# accessor, mutator, fieldname
DC_MAPPING = (
    ('Title', 'setTitle', None),
    ('Creator', None, None),
    ('Subject', 'setSubject', 'subject'),
    ('Description', 'setDescription', 'description'),
    ('Publisher', None, None),
    ('Contributors', 'setContributors', 'contributors'),
    ('Date', None, None),
    ('CreationDate', None, None),
    ('EffectiveDate', 'setEffectiveDate', 'effectiveDate'),
    ('ExpirationDate', 'setExpirationDate', 'expirationDate'),
    ('ModificationDate', None, None),
    ('Type', None, None),
    ('Format', 'setFormat', None),
    ('Identifier', None, None),
    ('Language', 'setLanguage', 'language'),
    ('Rights', 'setRights', 'rights'),

    # allowDiscussion is not part of the official DC metadata set
    #('allowDiscussion','isDiscussable','allowDiscussion'),
  )

# Mapping used from DC migration
METADATA_MAPPING = []
for accessor, mutator, field in DC_MAPPING:
    if accessor and mutator:
        METADATA_MAPPING.append((accessor, mutator))


def copyPermMap(old):
    """bullet proof copy
    """
    new = PersistentMapping()
    for k, v in old.items():
        new[k] = v
    return new


def getPermissionMapping(acperm):
    """Converts the list from ac_inherited_permissions into a dict
    """
    result = {}
    for entry in acperm:
        result[entry[0]] = entry[1]
    return result


class BaseMigrator(object):
    """Migrates an object to the new type

    The base class has the following attributes:

     * src_portal_type
       The portal type name the migration is migrating *from*
       Can be overwritten in the constructor
     * src_meta_type
       The meta type of the src object
     * dst_portal_type
       The portal type name the migration is migrating *to*
       Can be overwritten in the constructor
     * dst_meta_type
       The meta type of the dst object
     * map
       A dict which maps old attributes/function names to new
     * old
       The old object which has to be migrated
     * new
       The new object created by the migration
     * parent
       The folder where the old objects lives
     * orig_id
       The id of the old objet before migration
     * old_id
       The id of the old object while migrating
     * new_id
       The id of the new object while and after the migration
     * kwargs
       A dict of additional keyword arguments applied to the migrator
    """
    src_portal_type = None
    src_meta_type = None
    dst_portal_type = None
    dst_meta_type = None
    map = {}

    def __init__(self, obj, src_portal_type=None, dst_portal_type=None,
                 **kwargs):
        self.old = aq_inner(obj)
        self.orig_id = self.old.getId()
        self.old_id = '%s_MIGRATION_' % self.orig_id
        self.new = None
        self.new_id = self.orig_id
        self.parent = aq_parent(self.old)
        if src_portal_type is not None:
            self.src_portal_type = src_portal_type
        if dst_portal_type is not None:
            self.dst_portal_type = dst_portal_type
        self.kwargs = kwargs

        # safe id generation
        while hasattr(aq_base(self.parent), self.old_id):
            self.old_id += 'X'
        msg = "%s (%s -> %s)" % (self.old.absolute_url(1), self.src_portal_type,
                                 self.dst_portal_type)
        LOG.debug(msg)

    def getMigrationMethods(self):
        """Calculates a nested list of callables used to migrate the old object
        """
        beforeChange = []
        methods = []
        lastmethods = []
        for name in dir(self):
            if name.startswith('beforeChange_'):
                method = getattr(self, name)
                if callable(method):
                    beforeChange.append(method)
            if name.startswith('migrate_'):
                method = getattr(self, name)
                if callable(method):
                    methods.append(method)
            if name.startswith('last_migrate_'):
                method = getattr(self, name)
                if callable(method):
                    lastmethods.append(method)

        afterChange = methods + [self.custom, self.finalize] + lastmethods
        return (beforeChange, afterChange, )

    def migrate(self, unittest=0):
        """Migrates the object
        """
        beforeChange, afterChange = self.getMigrationMethods()

        # Unlock according to plone.locking:
        lockable = ILockable(self.old, None)
        if lockable and lockable.locked():
            lockable.unlock()
        # Unlock according to webdav:
        if self.old.wl_isLocked():
            self.old.wl_clearLocks()

        for method in beforeChange:
            __traceback_info__ = (self, method, self.old, self.orig_id)
            # may raise an exception, catch it later
            method()
        # preserve position on rename
        self.need_order = IOrderedContainer.providedBy(self.parent)
        if self.need_order:
            self._position = self.parent.getObjectPosition(self.orig_id)
        self.renameOld()
        self.createNew()

        for method in afterChange:
            __traceback_info__ = (self, method, self.old, self.orig_id)
            # may raise an exception, catch it later
            method()

        self.reorder()
        self.remove()

    __call__ = migrate

    def renameOld(self):
        """Renames the old object

        Must be implemented by the real Migrator
        """
        raise NotImplementedError

    def createNew(self):
        """Create the new object

        Must be implemented by the real Migrator
        """
        raise NotImplementedError

    def custom(self):
        """For custom migration
        """
        pass

    def migrate_properties(self):
        """Migrates zope properties

        Removes the old (if exists) and adds a new
        """
        if not hasattr(aq_base(self.old), 'propertyIds') or \
          not hasattr(aq_base(self.new), '_delProperty'):
            # no properties available
            return None

        for id in self.old.propertyIds():
            if id in ('title', 'description', 'content_type', ):
                # migrated by dc or other
                continue
            value = self.old.getProperty(id)
            typ = self.old.getPropertyType(id)
            __traceback_info__ = (self.new, id, value, typ)
            if self.new.hasProperty(id):
                self.new._delProperty(id)
            # continue if the object already has this attribute
            if getattr(aq_base(self.new), id, _marker) is not _marker:
                continue
            try:
                self.new._setProperty(id, value, typ)
            except ConflictError:
                raise
            except:
                LOG.error('Failed to set property %s type %s to %s at object %s' %
                          (id, typ, value, self.new), exc_info=True)

    def migrate_owner(self):
        """Migrates the zope owner
        """
        # getWrappedOwner is not always available
        if hasattr(aq_base(self.old), 'getWrappedOwner'):
            owner = self.old.getWrappedOwner()
            self.new.changeOwnership(owner)
        else:
            # fallback
            # not very nice but at least it works
            # trying to get/set the owner via getOwner(), changeOwnership(...)
            # did not work, at least not with plone 1.x, at 1.0.1, zope 2.6.2
            self.new._owner = self.old.getOwner(info=1)

    def migrate_localroles(self):
        """Migrate local roles
        """
        self.new.__ac_local_roles__ = None
        # Clean the auto-generated creators by Archetypes
        # ExtensibleMetadata.  Do set the original creators.
        self.new.setCreators(self.old.listCreators())
        local_roles = self.old.__ac_local_roles__
        if not local_roles:
            # Only set owner local role if the owner can be retrieved
            owner = self.old.getWrappedOwner()
            if owner is not SpecialUsers.nobody:
                self.new.manage_setLocalRoles(owner.getId(), ['Owner'])
        else:
            self.new.__ac_local_roles__ = copy(local_roles)
            if hasattr(self.old, '__ac_local_roles_block__'):
                self.new.__ac_local_roles_block__ = (
                    self.old.__ac_local_roles_block__)

    def migrate_user_roles(self):
        """Migrate roles added by users
        """
        if getattr(aq_base(self.old), 'userdefined_roles', False):
            ac_roles = self.old.userdefined_roles()
            new_ac_roles = tuple(getattr(self.new, '__ac_roles__', ()))
            if ac_roles:
                for role in ac_roles:
                    if role not in new_ac_roles:
                        self.new._addRole(role)

    def migrate_permission_settings(self):
        """Migrate permission settings (permission <-> role)
        The acquire flag is coded into the type of the sequence. If roles is a list
        than the roles are also acquire. If roles is a tuple the roles aren't
        acquired.
        """
        oldmap = getPermissionMapping(self.old.ac_inherited_permissions(1))
        newmap = getPermissionMapping(self.new.ac_inherited_permissions(1))
        for key, values in oldmap.items():
            old_p = Permission(key, values, self.old)
            old_roles = old_p.getRoles()
            new_values = newmap.get(key, ())
            new_p = Permission(key, new_values, self.new)
            new_p.setRoles(old_roles)

    def migrate_withmap(self):
        """Migrates other attributes from obj.__dict__ using a map

        The map can contain both attribute names and method names

        'oldattr' : 'newattr'
            new.newattr = oldattr
        'oldattr' : ''
            new.oldattr = oldattr
        'oldmethod' : 'newattr'
            new.newattr = oldmethod()
        'oldattr' : 'newmethod'
            new.newmethod(oldatt)
        'oldmethod' : 'newmethod'
            new.newmethod(oldmethod())
        """
        for oldKey, newKey in self.map.items():
            #LOG("oldKey: " + str(oldKey) + ", newKey: " + str(newKey))
            if not newKey:
                newKey = oldKey
            oldVal = getattr(self.old, oldKey)
            newVal = getattr(self.new, newKey)
            if callable(oldVal):
                value = oldVal()
            else:
                value = oldVal
            if callable(newVal):
                newVal(value)
            else:
                setattr(self.new, newKey, value)

    def remove(self):
        """Removes the old item

        Must be implemented by the real Migrator
        """
        raise NotImplementedError

    def reorder(self):
        """Reorder the new object in its parent

        Must be implemented by the real Migrator
        """
        raise NotImplementedError

    def finalize(self):
        """Finalize construction (called between)
        """
        ob = self.new
        fti = self.new.getTypeInfo()
        # This calls notifyWorkflowCreated which resets the migrated workflow
        # fti._finishConstruction(self.new)

        # _setPortalTypeName is required to
        if hasattr(ob, '_setPortalTypeName'):
            ob._setPortalTypeName(fti.getId())

        #self.new.reindexObject(['meta_type', 'portal_type'], update_metadata=False)


class BaseCMFMigrator(BaseMigrator):
    """Base migrator for CMF objects
    """

    def migrate_dc(self):
        """Migrates dublin core metadata
           This needs to be done after custom migrations, as you cannot
           setContentType on Images and Files until there is an object stored.
        """
        for accessor, mutator in METADATA_MAPPING:
            oldAcc = getattr(self.old, accessor)
            newMut = getattr(self.new, mutator)
            oldValue = oldAcc()
            newMut(oldValue)

    def migrate_workflow(self):
        """migrate the workflow state
        """
        wfh = getattr(self.old, 'workflow_history', None)
        if wfh:
            wfh = copyPermMap(wfh)
            self.new.workflow_history = wfh

    def migrate_allowDiscussion(self):
        """migrate allow discussion bit
        """
        if getattr(aq_base(self.old), 'allowDiscussion', _marker) is not _marker and \
          getattr(aq_base(self.new), 'isDiscussable', _marker)  is not _marker:
            self.new.isDiscussable(self.old.allowDiscussion())

    def migrate_discussion(self):
        """migrate talkback discussion bit
        """
        talkback = getattr(self.old.aq_inner.aq_explicit, 'talkback', _marker)
        if talkback is _marker:
            return
        else:
            self.new.talkback = talkback

    def beforeChange_storeDates(self):
        """Save creation date and modification date
        """
        self.old_creation_date = self.old.CreationDate()
        self.old_mod_date = self.old.ModificationDate()

    def last_migrate_date(self):
        """migrate creation / last modified date

        Must be called as *last* migration
        """
        self.new.creation_date = DateTime(self.old_creation_date)
        self.new.setModificationDate(DateTime(self.old_mod_date))

    def beforeChange_redirects(self):
        """Load redirects."""
        if IRedirectionStorage is None:
            return
        storage = queryUtility(IRedirectionStorage)
        if storage is None:
            return
        path = '/'.join(self.old.getPhysicalPath())
        self.old_redirects = storage.redirects(path)

    def migrate_redirects(self):
        """migrate redirects
        """
        if IRedirectionStorage is None:
            return
        storage = queryUtility(IRedirectionStorage)
        if storage is None:
            return
        path = '/'.join(self.new.getPhysicalPath())
        for redirect in self.old_redirects:
            storage.add(redirect, path)


class ItemMigrationMixin(object):
    """Migrates a non folderish object
    """
    isFolderish = False

    def renameOld(self):
        """Renames the old object
        """
        #LOG("renameOld | orig_id: " + str(self.orig_id) + "; old_id: " + str(self.old_id))
        #LOG(str(self.old.absolute_url(1)))
        unrestricted_rename(self.parent, self.orig_id, self.old_id)
        #self.parent.manage_renameObject(self.orig_id, self.old_id)

    def createNew(self):
        """Create the new object
        """
        _createObjectByType(self.dst_portal_type, self.parent, self.new_id)
        self.new = getattr(aq_inner(self.parent).aq_explicit, self.new_id)

    def remove(self):
        """Removes the old item
        """
        self.parent.manage_delObjects([self.old_id])

    def reorder(self):
        """Reorder the new object in its parent
        """
        if self.need_order:
            try:
                self.parent.moveObject(self.new_id, self._position)
            except ConflictError:
                raise
            except:
                LOG.error('Failed to reorder object %s in %s' % (self.new,
                          self.parent), exc_info=True)


class FolderMigrationMixin(ItemMigrationMixin):
    """Migrates a folderish object
    """
    isFolderish = True

    def beforeChange_patchNotifyWorkflowCreatedMethod(self):
        def notifyWorkflowCreated(self):
            """
              Do not notifyWorkflowCreated...
            """
            pass

        patch(WorkflowAware, 'notifyWorkflowCreated', notifyWorkflowCreated)

    def beforeChange_storeSubojects(self):
        """store subobjects from old folder
        This methods gets all subojects from the old folder and removes them from the
        old. It also preservers the folder order in a dict.
        For performance reasons the objects are removed from the old folder before it
        is renamed. Elsewise the objects would be reindex more often.
        """

        orderAble = IOrderedContainer.providedBy(self.old)
        orderMap = {}
        subobjs = {}

        # using objectIds() should be safe with BrokenObjects
        for id in self.old.objectIds():
            obj = getattr(self.old.aq_inner.aq_explicit, id)
            # Broken object support. Maybe we are able to migrate them?
            if isinstance(obj, BrokenClass):
                LOG.warning('BrokenObject in %s' % self.old.absolute_url(1))
                #continue

            if orderAble:
                try:
                    orderMap[id] = self.old.getObjectPosition(id) or 0
                except AttributeError:
                    LOG.debug("Broken OrderSupport", exc_info=True)
                    orderAble = 0
            subobjs[id] = aq_base(obj)
            # delOb doesn't call manage_afterAdd which safes some time because it
            # doesn't unindex an object. The migrate children method uses
            # _setObject later. This methods indexes the object again and
            # so updates all catalogs.
        for id in self.old.objectIds():
            # Loop again to remove objects, order is not preserved when
            # deleting objects
            self.old._delOb(id)
            # We need to take care to remove the relevant ids from _objects
            # otherwise objectValues breaks.
            if getattr(self.old, '_objects', None) is not None:
                self.old._objects = tuple([o for o in self.old._objects
                                           if o['id'] != id])

        self.orderMap = orderMap
        self.subobjs = subobjs
        self.orderAble = orderAble

    def migrate_children(self):
        """Copy childish objects from the old folder to the new one
        """
        subobjs = self.subobjs
        for id, obj in subobjs.items():
            # we have to use _setObject instead of _setOb because it adds the object
            # to folder._objects but also reindexes all objects.
            __traceback_info__ = __traceback_info__ = ('migrate_children',
                          self.old, self.orig_id, 'Migrating subobject %s' % id)
            try:
                self.new._setObject(id, obj, set_owner=0)
            except BadRequest:
                # If we already have the object we need to remove it carefully
                # and retry.  We can assume that such an object must be
                # autogenerated by a prior migration step and thus is less
                # correct than the original.  Such objects may want to
                # consider setting the attribute '__replaceable__' to avoid
                # this.
                if id in self.new.objectIds():
                    self.new._delOb(id)
                    if getattr(self.new, '_objects', None) is not None:
                        self.new._objects = tuple([o for o in
                                        self.new._objects if o['id'] != id])
                    self.new._setObject(id, obj, set_owner=0)
                else:
                    raise

        # reorder items
        # in CMF 1.5 Topic is orderable while ATCT's Topic is not orderable
        # order objects only when old *and* new are orderable we can't check
        # when creating the map because self.new == None.
        if self.orderAble and IOrderedContainer.providedBy(self.new):
            orderMap = self.orderMap
            for id, pos in orderMap.items():
                self.new.moveObjectToPosition(id, pos)

    def last_migrate_restoreNotifyWorkflowCreatedMethod(self):
        undoPatch(WorkflowAware, 'notifyWorkflowCreated')


class UIDMigrator(object):
    """Migrator class for migration CMF and AT uids
    """

    def migrate_cmf_uid(self):
        """Migrate CMF uids
        """
        uidhandler = getToolByName(self.parent, 'portal_uidhandler', None)
        if uidhandler is None:
            return  # no uid handler available
        uid = uidhandler.queryUid(self.old, default=None)
        if uid is not None:
            uidhandler.setUid(self.new, uid, check_uniqueness=False)

    def migrate_at_uuid(self):
        """Migrate AT universal uid
        """
        if not IReferenceable.providedBy(self.old):
            return  # old object doesn't support AT uuids
        uid = self.old.UID()
        self.old._uncatalogUID(self.parent)
        if UUID_ATTR:  # Prevent object deletion triggering UID related magic
            setattr(self.old, UUID_ATTR, None)
        if queryAdapter(self.new, IMutableUUID):
            IMutableUUID(self.new).set(str(uid))
        else:
            self.new._setUID(uid)


class CMFItemMigrator(ItemMigrationMixin, UIDMigrator, BaseCMFMigrator):
    """Migrator for items implementing the CMF API
    """


class CMFFolderMigrator(FolderMigrationMixin, UIDMigrator, BaseCMFMigrator):
    """Migrator from folderish items implementing the CMF API
    """
