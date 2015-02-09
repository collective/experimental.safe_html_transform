"""Support for migrators that load all values to be migrated into the
migrator, then delete the old object and then load the values into the
new object without requiring that the old object be renamed or
moved."""

from copy import copy

from Acquisition import aq_base
from ZODB.POSException import ConflictError
from AccessControl.Permission import Permission
from AccessControl import SpecialUsers

from Products.CMFCore.utils import getToolByName

from Products.Archetypes.interfaces import IReferenceable

from Products.contentmigration.basemigrator.migrator import BaseMigrator
from Products.contentmigration.basemigrator.migrator import BaseCMFMigrator
from Products.contentmigration.basemigrator.migrator import ItemMigrationMixin
from Products.contentmigration.basemigrator.migrator import FolderMigrationMixin
from Products.contentmigration.basemigrator.migrator import METADATA_MAPPING
from Products.contentmigration.basemigrator.migrator import getPermissionMapping
from Products.contentmigration.basemigrator.migrator import copyPermMap
from Products.contentmigration.basemigrator.migrator import LOG

_marker = []

class BaseInplaceMigrator(BaseMigrator):
    """Support for migrators that load all values to be migrated into the
    migrator, then delete the old object and then load the values into
    the new object without requiring that the old object be renamed or
    moved."""

    _properties = ()
    _properties_ignored = ('title', 'description', 'content_type', )

    def _checkLoadAttr(self, attr):
        """Check for an attribute on the migrator before loading and
        raise an error if it's already there."""
        if hasattr(self, attr):
            raise ValueError, ('The migrator already has a value '
                               'for %s.' % attr)

    def beforeChange_properties(self):
        """Load up the migrator with property values."""

        if not hasattr(aq_base(self.old), 'propertyIds'):
            # no properties available
            return None

        for id in self.old.propertyIds():
            if id in self._properties_ignored:
                # migrated by dc or other
                continue
            self._checkLoadAttr(id)

            value = self.old.getProperty(id)
            typ = self.old.getPropertyType(id)

            self._properties += ({'id': id,
                                  'type': typ,
                                  'value': value},)

    def migrate_properties(self):
        """Migrates zope properties

        Removes the old (if exists) and adds a new
        """
        if not hasattr(aq_base(self.new), '_delProperty'):
            # no properties available
            return None

        for prop_d in self._properties:
            id = prop_d['id']
            value = prop_d['value']
            typ = prop_d['type']
            __traceback_info__ = (self.new, id, value, typ)
            if self.new.hasProperty(id):
                self.new._delProperty(id)

            # continue if the object already has this attribute
            if getattr(aq_base(self.new), id, _marker) is not _marker:
                continue
            try:
                self.new.manage_addProperty(id, value, typ)
            except ConflictError:
                raise
            except:
                LOG.error('Failed to set property %s type %s to %s '
                          'at object %s' % (id, typ, value, self.new),
                          exc_info=True)

    def beforeChange_owner(self):
        """Load the zope owner."""
        self._checkLoadAttr('owner')
        self._checkLoadAttr('_owner')

        # getWrappedOwner is not always available
        if hasattr(aq_base(self.old), 'getWrappedOwner'):
            self.owner = self.old.getWrappedOwner()
        else:
            # fallback: not very nice but at least it works trying to
            # get/set the owner via getOwner(), changeOwnership(...)
            # did not work, at least not with plone 1.x, at 1.0.1,
            # zope 2.6.2
            self._owner = self.old.getOwner(info = 1)

    def migrate_owner(self):
        """Migrates the zope owner."""
        if hasattr(self, 'owner'):
            self.new.changeOwnership(self.owner)
        else:
            self.new._owner = self._owner

    def beforeChange_localroles(self):
        """Load local roles."""
        self._checkLoadAttr('__ac_local_roles__')
        self._checkLoadAttr('__ac_local_roles_block__')
        self.__ac_local_roles__ = self.old.__ac_local_roles__
        if hasattr(self.old, '__ac_local_roles_block__'):
            self.__ac_local_roles_block__ = (
                self.old.__ac_local_roles_block__)

    def migrate_localroles(self):
        """Migrate local roles
        """
        self.new.__ac_local_roles__ = None
        # Clean the auto-generated creators by Archetypes
        # ExtensibleMetadata.  Do set the original creators.
        self.new.setCreators(self.old.listCreators())
        if not self.__ac_local_roles__:
            # Only set owner local role if the owner can be retrieved
            if self.owner is not SpecialUsers.nobody:
                self.new.manage_setLocalRoles(
                    self.owner.getId(), ['Owner'])
        else:
            self.new.__ac_local_roles__ = copy(
                self.__ac_local_roles__)
            if hasattr(self, '__ac_local_roles_block__'):
                self.new.__ac_local_roles_block__ = (
                    self.__ac_local_roles_block__)

    def beforeChange_permission_settings(self):
        """Load permission settings (permission <-> role)."""
        self._checkLoadAttr('ac_inherited_permissions')
        self.ac_inherited_permissions = getPermissionMapping(
            self.old.ac_inherited_permissions(1))

    def migrate_permission_settings(self):
        """Migrate permission settings (permission <-> role)

        The acquire flag is coded into the type of the sequence. If roles is a list
        than the roles are also acquire. If roles is a tuple the roles aren't
        acquired.
        """
        _marker = []

        oldmap = self.ac_inherited_permissions
        newmap = getPermissionMapping(self.new.ac_inherited_permissions(1))
        for key, values in oldmap.items():
            old_p = Permission(key, values, self.old)
            old_roles = old_p.getRoles(default=_marker)
            if old_roles is _marker:
                continue
            new_values = newmap.get(key, ())
            new_p = Permission(key, new_values, self.new)
            new_p.setRoles(old_roles)

    def beforeChange_withmap(self):
        """Loads other attributes from obj.__dict__.  See migrat_withmap."""

        for oldKey, newKey in self.map.items():
            if not newKey:
                newKey = oldKey
                self._checkLoadAttr(newKey)

            oldVal = getattr(self.old, oldKey)
            if callable(oldVal):
                value = oldVal()
            else:
                value = oldVal

            setattr(self, newKey, value)

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
            new.newmethod(oldmethod())"""
        for newKey in self.map.values():
            newVal = getattr(self.new, newKey)
            value = getattr(self, newKey)
            if callable(newVal):
                newVal(value)
            else:
                setattr(self.new, newKey, value)

class BaseInplaceCMFMigrator(BaseInplaceMigrator, BaseCMFMigrator):
    """Support for CMF migration that doesn't require renaming the old
    object."""

    def beforeChange_dc(self):
        """Load dublin core metadata."""
        for accessor, mutator in METADATA_MAPPING:
            self._checkLoadAttr(mutator)

            oldAcc = getattr(self.old, accessor)
            oldValue = oldAcc()
            setattr(self, mutator, oldValue)

    def migrate_dc(self):
        """Migrates dublin core metadata This needs to be done after
        custom migrations, as you cannot setContentType on Images and
        Files until there is an object stored.  """
        for accessor, mutator in METADATA_MAPPING:
            newMut = getattr(self.new, mutator)
            oldValue = getattr(self, mutator)
            newMut(oldValue)

    def beforeChange_workflow(self):
        """Load the workflow state."""
        self._checkLoadAttr('workflow_history')
        self.workflow_history = getattr(self.old, 'workflow_history',
                                        None)

    def migrate_workflow(self):
        """migrate the workflow state."""
        wfh = self.workflow_history
        if wfh:
            wfh = copyPermMap(wfh)
            self.new.workflow_history = wfh

    def beforeChange_allowDiscussion(self):
        """load allow discussion bit."""
        self._checkLoadAttr('isDiscussable')
        if (getattr(aq_base(self.old), 'allowDiscussion', _marker) is
            not _marker):
            self.isDiscussable = self.old.allowDiscussion()

    def migrate_allowDiscussion(self):
        """migrate allow discussion bit."""
        if (getattr(aq_base(self.new), 'isDiscussable', _marker)
            is not _marker and hasattr(self, 'isDiscussable')):
            self.new.isDiscussable(self.isDiscussable)

    def beforeChange_discussion(self):
        """Load talkback discussion bit."""
        self._checkLoadAttr('talkback')
        self.talkback = getattr(self.old.aq_inner.aq_explicit,
                                'talkback', _marker)

    def migrate_discussion(self):
        """migrate talkback discussion bit
        """
        if self.talkback is _marker:
            return
        else:
            self.new.talkback = self.talkback

class InplaceItemMigrationMixin(ItemMigrationMixin):
    """Migrates a non folderish object."""

    def renameOld(self):
        """Remove the old object rather than rename it."""
        self.parent.manage_delObjects([self.orig_id])

    def remove(self):
        """Since we remove where other migrators rename, we pass
        here."""
        pass

class InplaceFolderMigrationMixin(InplaceItemMigrationMixin,
                                  FolderMigrationMixin):
    """Migrates a folderish object inplace."""
    isFolderish = True

class InplaceUIDMigrator(object):
    """Inplace Migrator class for migration CMF and AT uids. """

    def beforeChange_cmf_uid(self):
        """Load CMF uids."""
        self._checkLoadAttr('uid')
        uidhandler = getToolByName(self.parent, 'portal_uidhandler',
                                   None)
        if uidhandler is not None:
            self.uid = uidhandler.queryUid(self.old, default=None)

    def migrate_cmf_uid(self):
        """Migrate CMF uids."""
        uidhandler = getToolByName(self.parent, 'portal_uidhandler', None)
        if uidhandler is not None:
            return # no uid handler available
        uid = self.uid
        if uid is not None:
            uidhandler.setUid(self.new, uid, check_uniqueness=False)

    def beforeChange_at_uuid(self):
        """Load AT universal uid."""
        self._checkLoadAttr('UID')
        if IReferenceable.providedBy(self.old):
            self.UID = self.old.UID()
            self.old._uncatalogUID(self.parent)
        else:
            self.UID = None

    def migrate_at_uuid(self):
        """Migrate AT universal uid
        """
        uid = self.UID
        if uid:
            self.new._setUID(uid)

class InplaceCMFItemMigrator(InplaceItemMigrationMixin,
                             InplaceUIDMigrator,
                             BaseInplaceCMFMigrator):
    """Inplace migrator for items implementing the CMF API."""
    pass

class InplaceCMFFolderMigrator(InplaceFolderMigrationMixin,
                               InplaceUIDMigrator,
                               BaseInplaceCMFMigrator):
    """Inplace migrator from folderish items implementing the CMF
    API."""
    pass
