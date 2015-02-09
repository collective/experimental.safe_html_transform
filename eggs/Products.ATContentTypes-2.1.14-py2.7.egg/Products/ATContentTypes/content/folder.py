from zope.interface import implements

from AccessControl import ClassSecurityInfo
from OFS.interfaces import IOrderedContainer

from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.content.base import registerATCT
from Products.ATContentTypes.content.base import ATCTOrderedFolder
from Products.ATContentTypes.content.base import ATCTBTreeFolder
from Products.ATContentTypes.interfaces import IATFolder
from Products.ATContentTypes.interfaces import IATBTreeFolder
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import NextPreviousAwareSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.lib.constraintypes import ConstrainTypesMixinSchema

from Products.CMFCore.permissions import View

from plone.app.folder import folder

ATFolderSchema = folder.ATFolderSchema
ObsoleteATFolderSchema = ATContentTypeSchema.copy() + ConstrainTypesMixinSchema + NextPreviousAwareSchema
ATBTreeFolderSchema = ATContentTypeSchema.copy() + ConstrainTypesMixinSchema

finalizeATCTSchema(folder.ATFolderSchema, folderish=True, moveDiscussion=False)
finalizeATCTSchema(ATBTreeFolderSchema, folderish=True, moveDiscussion=False)

HAS_LINGUAPLONE = True
try:
    from Products.LinguaPlone.I18NBaseBTreeFolder import I18NOnlyBaseBTreeFolder
except ImportError:
    HAS_LINGUAPLONE = False


class ObsoleteATFolder(ATCTOrderedFolder):
    """A folder which can contain other items."""

    schema = folder.ATFolderSchema

    portal_type = 'Folder'
    archetype_name = 'Folder'
    _atct_newTypeFor = {'portal_type': 'CMF Folder', 'meta_type': 'Plone Folder'}
    assocMimetypes = ()
    assocFileExt = ()
    cmf_edit_kws = ()

    implements(IATFolder, IOrderedContainer)

    # Enable marshalling via WebDAV/FTP.
    __dav_marshall__ = True

    security = ClassSecurityInfo()

    security.declareProtected(View, 'getNextPreviousParentValue')
    def getNextPreviousParentValue(self):
        """If the parent node is also an IATFolder and has next/previous
        navigation enabled, then let this folder have it enabled by
        default as well.
        """
        parent = self.__parent__
        if IATFolder.providedBy(parent):
            return parent.getNextPreviousEnabled()
        else:
            return False


registerATCT(ObsoleteATFolder, PROJECTNAME)


FOLDER_MANAGE_OPTIONS = (
 {'action': 'manage_main', 'label': 'Contents'},
 {'action': '', 'label': 'View'},
 {'action': 'manage_interfaces', 'label': 'Interfaces'},
)


if HAS_LINGUAPLONE:
    class ATFolder(I18NOnlyBaseBTreeFolder, folder.ATFolder):
        """A folder which can contain other items."""
        portal_type = 'Folder'
        manage_options = FOLDER_MANAGE_OPTIONS
        security = ClassSecurityInfo()

        security.declarePrivate('manage_beforeDelete')
        def manage_beforeDelete(self, item, container):
            I18NOnlyBaseBTreeFolder.manage_beforeDelete(self, item, container)
            folder.ATFolder.manage_beforeDelete(self, item, container)

else:
    class ATFolder(folder.ATFolder):
        """A folder which can contain other items."""
        portal_type = 'Folder'
        manage_options = FOLDER_MANAGE_OPTIONS


registerATCT(ATFolder, PROJECTNAME)


class ATBTreeFolder(ATCTBTreeFolder):
    """A folder suitable for holding a very large number of items.

    Note -- DEPRECATED.  Will be removed in Plone 5.
    Normal folders (as implemented in plone.app.folder) are now suitable for
    storing large numbers of items in most cases.  If you need a folder that
    doesn't track order at all, use a normal folder (from plone.app.folder)
    with the ordering attribute set to u'unordered'.
    """
    schema = ATBTreeFolderSchema

    portal_type = 'Large Plone Folder'
    archetype_name = 'Large Folder'
    _atct_newTypeFor = {'portal_type': 'CMF Large Plone Folder',
                        'meta_type': 'Large Plone Folder'}
    assocMimetypes = ()
    assocFileExt = ()
    cmf_edit_kws = ()

    implements(IATBTreeFolder)

    # Enable marshalling via WebDAV/FTP.
    __dav_marshall__ = True

    security = ClassSecurityInfo()

registerATCT(ATBTreeFolder, PROJECTNAME)
