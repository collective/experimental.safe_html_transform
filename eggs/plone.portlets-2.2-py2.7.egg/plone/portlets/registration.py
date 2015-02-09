from zope.interface import implements
from persistent import Persistent

from plone.portlets.interfaces import IPortletType


class PortletType(Persistent):
    """A portlet registration.

    This is persistent so that it can be stored as a local utility.
    """
    implements(IPortletType)

    title = u''
    description = u''
    addview = u''
    editview = None
    for_ = None
