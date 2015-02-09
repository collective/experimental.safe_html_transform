from Products.ATContentTypes.migration.walker import CatalogWalker
from wicked.at.migration.migrator import WickedDocMigrator
from Products.CMFCore.utils import getToolByName

def migrate_atdoc_wickeddoc(self):
    catalog = getToolByName(self, 'portal_catalog')
    portal = getToolByName(self, 'portal_url').getPortalObject()
    out = []

    migrator = WickedDocMigrator
    out.append('*** Migrating %s to %s ***\n' % (migrator.src_portal_type,
                                                 migrator.dst_portal_type))
    try:
        w = CatalogWalker(migrator, portal) # ATCT-0.2
    except AttributeError:
        w = CatalogWalker(portal, migrator) # ATCT-1.0
    w_result = w.go()
    if type(w_result) == type(''):
        out.append(w_result) # ATCT-0.2
    else:
        out.append('%s Migrated\n' % migrator.src_portal_type)

    wf = getToolByName(self, 'portal_workflow')
    count = wf.updateRoleMappings()
    out.append('Workflow: %d object(s) updated.' % count)

    catalog.refreshCatalog(clear=1)
    out.append('Portal catalog updated.')

    ttool = getToolByName(self, 'portal_types')
    doc_fti = ttool.getTypeInfo('Document')
    if doc_fti.Metatype() != 'WickedDoc':
        atct_tool = getToolByName(self, 'portal_atct')
        get_transaction().commit(1)
        atct_tool._changePortalTypeName('Document', 'ATDocument',
                                        global_allow=0,
                                        title='AT Document')
        get_transaction().commit(1)
        atct_tool._changePortalTypeName('WickedDoc', 'Document',
                                        global_allow=1,
                                        title='Page')
        out.append('Document types switched')

    return '\n'.join(out)
