try:
    from Products.ATContentTypes.migration.migrator import CMFItemMigrator
    from Products.ATContentTypes.migration.common import registerMigrator
    from Products.ATContentTypes.migration.walker import CatalogWalker
except ImportError:
    CMFItemMigrator = None

if CMFItemMigrator != None:
    class WickedDocMigrator(CMFItemMigrator):
        walker = CatalogWalker
        map = {'getText': 'setText'}

        src_portal_type = 'Document'
        src_meta_type = 'ATDocument'
        dst_portal_type = 'WickedDoc'
        dst_meta_type = 'WickedDoc'

        def custom(self):
            self.new.setContentType(self.old.getContentType())

    registerMigrator(WickedDocMigrator)
