from zope.interface import implementer
from zope.component import adapter
from Products.Archetypes.interfaces import IBaseObject
from wicked.interfaces import IUID


def initialize(context):
    """init for wicked.at"""
    pass


@implementer(IUID)
@adapter(IBaseObject)
def at_uid(atobj):
    return atobj.UID()
