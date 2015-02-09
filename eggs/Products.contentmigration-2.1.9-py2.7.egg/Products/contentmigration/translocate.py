"""Support for migrators that place the destination object in a
different location from the source object."""

import logging
from Acquisition import aq_inner
from ZODB.POSException import ConflictError

from Products.contentmigration.common import _createObjectByType

from Products.contentmigration.inplace import (InplaceCMFItemMigrator,
                                               InplaceCMFFolderMigrator)
logger = logging.getLogger(__name__)

class TranslocatingMigratorMixin(object):
    """A migrator that places the destination object in a different
    location from the source object."""

    def getDestinationParent(self):
        """Return the container into which the destination will be
        added."""
        return self.parent

    def createNew(self):
        """Create the new object
        """
        dst_parent = self.getDestinationParent()

        # Support AT migration if used
        schema = getattr(self, 'schema', {})

        _createObjectByType(self.dst_portal_type, dst_parent,
                            self.new_id, **schema)
        self.new = getattr(aq_inner(dst_parent).aq_explicit, self.new_id)

    def reorder(self):
        """Reorder in the right parent.
        """
        if self.need_order:
            try:
                self.getDestinationParent().moveObject(
                    self.new_id, self._position)
            except ConflictError:
                raise
            except:
                logger.error('Failed to reorder object %s in %s' % (self.new,
                          self.parent), exc_info=True)

class TranslocatingInplaceCMFItemMigrator(TranslocatingMigratorMixin,
                                          InplaceCMFItemMigrator):
    """Inplace migrator for items implementing the CMF API."""
    pass

class TranslocatingInplaceCMFFolderMigrator(
    TranslocatingMigratorMixin, InplaceCMFFolderMigrator):
    """Inplace migrator for folders implementing the CMF API."""
    pass

# BBB: Not sure why these below were done this way, but they are in
# use by remember so I'm leaving them here.

from Products.contentmigration.basemigrator.migrator import UIDMigrator
from Products.contentmigration.inplace import InplaceUIDMigrator

class TranslocatingInplaceMigrator(TranslocatingMigratorMixin,
                                   InplaceUIDMigrator):
    """UID migration support for inplace translocating migrators."""
    pass

class TranslocatingMigrator(TranslocatingMigratorMixin,
                            UIDMigrator):
    """UID migration support for translocating migrators."""
    pass
