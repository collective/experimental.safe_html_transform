from zope.interface import implements
from zope.container.ordered import OrderedContainer

from plone.contentrules.engine.interfaces import IRuleStorage

from BTrees.OOBTree import OOBTree

class RuleStorage(OrderedContainer):
    """A container for rules.
    """

    implements(IRuleStorage)

    active = True

    def __init__(self):
        # XXX: This depends on implementation detail in OrderedContainer,
        # but it uses a PersistentDict, which sucks :-/
        OrderedContainer.__init__(self)
        self._data = OOBTree()
