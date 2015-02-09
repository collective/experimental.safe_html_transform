from Products.CMFCore.utils import getToolByName
from cStringIO import StringIO
from wicked.at import config
from wicked.at.config import REFERENCE_MANAGER

def configureWysiwyg(portal, out):
    props = getToolByName(portal, 'portal_properties')
    if not hasattr(props, 'site_properties'): # not plone
        return

    editors = props.site_properties.getProperty('available_editors')
    if "Kupu" in editors:
        # move it up in the list
        editors = list(editors)
        editors.remove('Kupu')
        editors = ['Kupu',] + editors
        props.site_properties._updateProperty('available_editors', editors)


def configureReferenceCatalog(portal, out):
    catalog = getToolByName(portal, REFERENCE_MANAGER)
    for indexName, indexType in (
        ('targetId', 'FieldIndex'),
        ('targetTitle', 'FieldIndex'),
        ('targetURL', 'FieldIndex'), ):

        try:
            catalog.addIndex(indexName, indexType, extra=None)
        except:
            pass
        try:
            catalog.addColumn(indexName)
        except:
            pass

        catalog.manage_reindexIndex(indexName)


def install(self):
    out = StringIO()
    configureReferenceCatalog(self, out)
    configureWysiwyg(self, out)
    reindex = None
    pc = getToolByName(self, 'portal_catalog')
    if not 'UID' in pc.schema():
        pc.addColumn('UID')
        reindex = True

    if not 'UID' in pc.indexes():
        pc.addIndex('UID', 'FieldIndex')
        reindex = True

    pc.manage_reindexIndex('UID')
    print >> out, "Successfully installed %s." % config.PROJECTNAME
    return out.getvalue()
