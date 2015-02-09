from zope.interface import Interface


# zope3 interfaces

try:
    from Products.ATContentTypes.interface.archive import IArchivable
    from Products.ATContentTypes.interface.image import IPhotoAlbumAble
    IArchivable, IPhotoAlbumAble    # keep pyflakes happy
except ImportError:
    class IArchivable(Interface):
        """ marker interface for now gone bbb import """
    class IPhotoAlbumAble(Interface):
        """ marker interface for now gone bbb import """


# zope2 interfaces

try:
    from OFS.IOrderSupport import IOrderedContainer as OFSOrderedContainer
    from Products.Archetypes.atapi import BaseFolder
    from Products.ATContentTypes.content.base import ATCTFolderMixin
    from Products.ATContentTypes.interfaces import IATFolder
    from Products.ATContentTypes.interfaces import IATBTreeFolder
    from Products.CMFPlone.interfaces.OrderedContainer import IOrderedContainer
    base_implements = (BaseFolder.__implements__,
                       OFSOrderedContainer, IOrderedContainer)
    folder_implements = (ATCTFolderMixin.__implements__, base_implements,
                         IATBTreeFolder, IATFolder)
except ImportError:
    base_implements = ()
    folder_implements = ()
