from zope.interface import Interface


class IImageContent(Interface):
    """Interface for types containing an image
    """

    def getImage(**kwargs):
        """
        """

    def setImage(value, **kwargs):
        """
        """

    def tag(**kwargs):
        """
        """


class IATImage(IImageContent):
    """AT Image marker Interface
    """
