from zope.interface import Interface


class ISessionPlugin(Interface):
    """Session handling PAS plugin.
    """

    def _setupSession(userid, response):
        """
        Start a new session for a userid. The session will last until
        PAS indicates that the user has logged out.
        """
