from zope.container.constraints import contains
from zope.container.interfaces import IContainer
from zope.interface import Attribute
from zope.interface.common.sequence import IFiniteSequence
from zope.location.interfaces import IContained



class IKeyManager(IContainer):
    contains("plone.keyring.interfaces.IKeyring")

    def clear(ring=u"_system"):
        """Clear all keys on a given ring. By default the system ring
        is cleader.  If None is used as ring id all rings are cleared.
        """

    def rotate(ring=u"_system"):
        """Rotate a given ring. By default rotates the system ring.
        If None is used as ring id all rings are rotated.
        """

    def secret(ring=u"_system"):
        """Return the current secret for a given ring. If no ring
        is given the secret for the system ring is returned"""
        


class IKeyring(IContained, IFiniteSequence):
    current = Attribute("The current (ie latest) secret in the ring.")

    def __init__(size=5):
        """Construct a new keyring for a specified number of keys.
        """

    def clear():
        """Remove all keys from the ring.
        """

    def rotate():
        """Add a new secret to the ring, pushing out the oldest secret.
        """

