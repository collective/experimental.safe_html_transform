from Acquisition import aq_base
from zope.interface import implements
from zope.component import adapts
from plone.folder.interfaces import IOrdering, IOrderableFolder


class UnorderedOrdering(object):
    """ This implementation provides no ordering. """
    implements(IOrdering)
    adapts(IOrderableFolder)

    def __init__(self, context):
        self.context = context

    def notifyAdded(self, id):
        pass

    def notifyRemoved(self, id):
        pass

    def idsInOrder(self):
        return aq_base(self.context).objectIds(ordered=False)

    def getObjectPosition(self, id):
        return None
