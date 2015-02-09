from Products.ATContentTypes.interfaces.document import IATDocument
from Products.ATContentTypes.interfaces.image import IImageContent


class IATNewsItem(IATDocument, IImageContent):
    """AT News Item marker interface
    """
