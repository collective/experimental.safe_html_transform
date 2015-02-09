from zope.interface import Interface


class IFileContent(Interface):
    """Interface for types containing a file
    """

    def getFile(**kwargs):
        """
        """

    def setFile(value, **kwargs):
        """
        """


class IATFile(IFileContent):
    """AT File marker interface
    """
