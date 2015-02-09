from zope.interface import implements
from zope.component import adapts

from z3c.caching.interfaces import IPurgePaths

from OFS.interfaces import ITraversable

class TraversablePurgePaths(object):
    """Default purge for OFS.Traversable-style objects
    """

    implements(IPurgePaths)
    adapts(ITraversable)

    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        return ['/' + self.context.virtual_url_path()]

    def getAbsolutePaths(self):
        return []
