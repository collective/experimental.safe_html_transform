from Acquisition import aq_inner
from zope.interface import alsoProvides, directlyProvidedBy

from Products.CMFCore.utils import getToolByName

from Products.Archetypes.ArchetypeTool import getType
from Products.Archetypes.config import REFERENCE_ANNOTATION
from Products.Archetypes.Referenceable import Referenceable

from Products.contentmigration.common import _createObjectByType

from Products.contentmigration.basemigrator.migrator import BaseCMFMigrator
from Products.contentmigration.basemigrator.migrator import ItemMigrationMixin
from Products.contentmigration.basemigrator.migrator import FolderMigrationMixin
from Products.contentmigration.basemigrator.migrator import UIDMigrator

from Products.contentmigration.inplace import BaseInplaceCMFMigrator
from Products.contentmigration.inplace import InplaceItemMigrationMixin
from Products.contentmigration.inplace import InplaceFolderMigrationMixin
from Products.contentmigration.inplace import InplaceUIDMigrator

from Products.contentmigration.translocate import TranslocatingMigratorMixin

_marker = []


def migrate_dummy(self):
    """Do nothing.  Used to override inherited methods we don't
    want to run."""
    pass


class ATMigratorMixin(object):
    """Migrates content of one AT type to another AT type."""

    fields_map = {}
    only_fields_map = False
    accessor_getter = 'getEditAccessor'

    # Override some methods from BaseCMFMigrator that we don't want to
    # run for AT migrations.
    migrate_dc = migrate_dummy
    migrate_allowDiscussion = migrate_dummy

    def beforeChange_storeDates(self):
        """Save creation date and modification date
        """
        old_schema = self.old.Schema()
        for field_name in ['creation_date', 'modification_date']:
            old_field = old_schema[field_name]
            accessor = (old_field.getEditAccessor(self.old) or
                        old_field.getAccessor(self.old))
            setattr(self, 'old_' + field_name, accessor())

    # XXX Can this be set through the call to the constructor?
    def last_migrate_date(self):
        """migrate creation / last modified date

        Must be called as *last* migration
        """
        new_schema = self.new.Schema()
        for field_name in ['creation_date', 'modification_date']:
            new_field = new_schema[field_name]
            mutator = new_field.getMutator(self.new)
            mutator(getattr(self, 'old_' + field_name))

    def beforeChange_references(self):
        """Migrate references annotation."""
        # Set the flag so that references aren't deleted
        self.old._v_cp_refs = 1
        # Move the references annotation storage
        if hasattr(self.old, REFERENCE_ANNOTATION):
            at_references = getattr(self.old, REFERENCE_ANNOTATION)
            setattr(self, REFERENCE_ANNOTATION, at_references)

    def migrate_references(self):
        """Migrate references annotation."""
        # Restor the references annotation
        if hasattr(self, REFERENCE_ANNOTATION):
            at_references = getattr(self, REFERENCE_ANNOTATION)
            setattr(self.new, REFERENCE_ANNOTATION, at_references)
        # Run the reference manage_afterAdd to transition all copied
        # references
        is_cp = getattr(self.old, '_v_is_cp', _marker)
        self.new._v_is_cp = 0
        Referenceable.manage_afterAdd(self.new, self.new,
                                      self.new.__parent__)
        if is_cp is not _marker:
            self.new._v_is_cp = is_cp
        else:
            del self.new._v_is_cp


class BaseATMigrator(ATMigratorMixin, BaseCMFMigrator):
    """Migrates content of one AT type to another AT type."""
    pass


class ATItemMigratorMixin(object):
    """Migrator for items implementing the AT API."""

    def beforeChange_schema(self):
        """Load the values of fields according to fields_map if present.

        Each key in fields_map is a field in the old schema and each
        value is a field in the new schema.  If fields_map isn't a
        mapping, each field in the old schema will be migrated into
        the new schema.  Obeys field modes for readable and writable
        fields.  These values are then passed in as field kwargs into
        the constructor in the createNew method."""

        old_schema = self.old.Schema()

        typesTool = getToolByName(self.parent, 'portal_types')
        fti = typesTool.getTypeInfo(self.dst_portal_type)
        archetype = getType(self.dst_meta_type, fti.product)
        new_schema = archetype['klass'].schema

        if self.only_fields_map:
            old_field_names = self.fields_map.keys()
        else:
            old_field_names = old_schema.keys()

        # Let the migrator handle the id and dates
        for omit_field_name in ['id', 'creation_date',
                                'modification_date']:
            if omit_field_name in old_field_names:
                old_field_names.remove(omit_field_name)

        kwargs = getattr(self, 'schema', {})
        for old_field_name in old_field_names:
            old_field = self.old.getField(old_field_name)
            new_field_name = self.fields_map.get(old_field_name,
                                                 old_field_name)

            if new_field_name is None:
                continue

            new_field = new_schema.get(new_field_name, None)
            if new_field is None:
                continue

            if ('r' in old_field.mode and 'w' in new_field.mode):
                accessor = (
                    getattr(old_field, self.accessor_getter)(self.old)
                    or old_field.getAccessor(self.old))
                value = accessor()
                kwargs[new_field_name] = value
        self.schema = kwargs

    def createNew(self):
        """Create the new object passing in the loaded archetypes
        schema field values as kwargs."""
        _createObjectByType(self.dst_portal_type, self.parent,
                            self.new_id, **self.schema)
        self.new = getattr(aq_inner(self.parent).aq_explicit,
                           self.new_id)

    def migrate_extension_fields(self):
        """Migrate extension fields.

        In the beforeChange_schema method only standard fields of the
        schema are taken care of.  Extension fields from
        archetypes.schemaextender are not handled.  This can only
        really be done after the new object has been created.
        """

        old_schema = self.old.Schema()
        typesTool = getToolByName(self.parent, 'portal_types')
        fti = typesTool.getTypeInfo(self.dst_portal_type)
        archetype = getType(self.dst_meta_type, fti.product)
        plain_new_schema = archetype['klass'].schema
        new_schema = self.new.Schema()

        if self.only_fields_map:
            old_field_names = self.fields_map.keys()
        else:
            old_field_names = old_schema.keys()

        kwargs = {}
        for old_field_name in old_field_names:
            old_field = self.old.getField(old_field_name)
            new_field_name = self.fields_map.get(old_field_name,
                                                 old_field_name)

            if new_field_name is None:
                continue
            if new_field_name in plain_new_schema.keys():
                # Already migrated.
                continue

            new_field = new_schema.get(new_field_name, None)
            if new_field is None:
                continue

            if ('r' in old_field.mode and 'w' in new_field.mode):
                accessor = (
                    getattr(old_field, self.accessor_getter)(self.old)
                    or old_field.getAccessor(self.old))
                value = accessor()
                kwargs[new_field_name] = value
        # Apply the changes.
        self.new.update(**kwargs)

    def migrate_marker_interfaces(self):
        """Migrate marker interfaces.
        """
        alsoProvides(self.new, directlyProvidedBy(self.old))


class ATItemMigrator(ATItemMigratorMixin, ItemMigrationMixin,
                     UIDMigrator, BaseATMigrator):
    """Migrator for items implementing the AT API."""
    pass


class ATFolderMigrator(ATItemMigratorMixin, FolderMigrationMixin, UIDMigrator,
                       BaseATMigrator):
    """Migrator from folderish items implementing the AT API."""
    pass

# Inplace migrators


class BaseInplaceATMigrator(ATMigratorMixin, BaseInplaceCMFMigrator):
    """Migrates content of one AT type to another AT type inplace."""
    pass


class InplaceATItemMigrator(ATItemMigratorMixin,
                            InplaceItemMigrationMixin,
                            InplaceUIDMigrator,
                            BaseInplaceATMigrator):
    """Migrator for items implementing the AT API."""
    pass


class InplaceATFolderMigrator(ATItemMigratorMixin,
                              InplaceFolderMigrationMixin,
                              InplaceUIDMigrator,
                              BaseInplaceATMigrator):
    """Migrator from folderish items implementing the AT API."""
    pass

# Translocating migrators


class TranslocatingInplaceATItemMigrator(TranslocatingMigratorMixin,
                                         InplaceATItemMigrator):
    """Inplace migrator for items implementing the AT API."""
    pass


class TranslocatingInplaceATFolderMigrator(TranslocatingMigratorMixin,
                                           InplaceATFolderMigrator):
    """Inplace migrator for folders implementing the AT API."""
    pass
