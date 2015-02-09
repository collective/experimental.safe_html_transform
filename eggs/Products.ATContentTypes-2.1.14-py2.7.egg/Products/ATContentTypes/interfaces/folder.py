from zope.interface import Interface
from Products.ATContentTypes.interfaces.interfaces import IATContentType
try:
    from Products.CMFPlone.interfaces.syndication import ISyndicatable
except ImportError:
    from zope.interface import Interface as ISyndicatable


class IFilterFolder(Interface):
    def listObjects():
        """
        """


class IATFolder(IATContentType, ISyndicatable):
    """AT Folder marker interface
    """


class IATBTreeFolder(IATContentType):
    """AT BTree Folder marker interface
    """
