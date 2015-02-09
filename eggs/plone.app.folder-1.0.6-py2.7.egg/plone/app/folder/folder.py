from AccessControl import ClassSecurityInfo
from zope.interface import implements
from Products.CMFCore.permissions import View
from Products.ATContentTypes.interface import IATFolder
from Products.ATContentTypes.interface import IATBTreeFolder
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import NextPreviousAwareSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.lib.constraintypes import \
    ConstrainTypesMixinSchema
from Products.ATContentTypes.content.base import ATCTFolderMixin
from Products.ATContentTypes.content.base import registerATCT

from plone.app.folder import packageName
from plone.app.folder.base import BaseBTreeFolder
from plone.app.folder.bbb import IArchivable, IPhotoAlbumAble
from plone.app.folder.bbb import folder_implements


ATFolderSchema = ATContentTypeSchema.copy() + \
    ConstrainTypesMixinSchema.copy() + NextPreviousAwareSchema.copy()
finalizeATCTSchema(ATFolderSchema, folderish=True, moveDiscussion=False)


class IATUnifiedFolder(IATFolder):
    """ marker interface for the new, unified folders """


class ATFolder(ATCTFolderMixin, BaseBTreeFolder):
    """ a folder suitable for holding a very large number of items """
    implements(IATUnifiedFolder, IATBTreeFolder, IArchivable, IPhotoAlbumAble)

    __implements__ = folder_implements

    schema = ATFolderSchema
    security = ClassSecurityInfo()

    portal_type = 'Folder'
    archetype_name = 'Folder'
    assocMimetypes = ()
    assocFileExt = ()
    cmf_edit_kws = ()

    # Enable marshalling via WebDAV/FTP/ExternalEditor.
    __dav_marshall__ = True

    security.declareProtected(View, 'getNextPreviousParentValue')
    def getNextPreviousParentValue(self):
        """ If the parent node is also an IATFolder and has next/previous
            navigation enabled, then let this folder have it enabled by
            default as well """
        parent = self.getParentNode()
        if IATFolder.providedBy(parent):
            return parent.getNextPreviousEnabled()
        else:
            return False


registerATCT(ATFolder, packageName)
