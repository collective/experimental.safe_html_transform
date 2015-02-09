from persistent.list import PersistentList
from BTrees.OIBTree import OIBTree

from zope.interface import implements
from zope.component import adapts
from zope.annotation.interfaces import IAnnotations
from zope.container.contained import notifyContainerModified

from plone.folder.interfaces import IOrderableFolder
from plone.folder.interfaces import IExplicitOrdering


class DefaultOrdering(object):
    """ This implementation uses annotations to store the order on the
        object, and supports explicit ordering. """

    implements(IExplicitOrdering)
    adapts(IOrderableFolder)

    ORDER_KEY = "plone.folder.ordered.order"
    POS_KEY = "plone.folder.ordered.pos"

    def __init__(self, context):
        self.context = context

    def notifyAdded(self, id):
        """ see interfaces.py """
        order = self._order(True)
        pos = self._pos(True)
        order.append(id)
        pos[id] = len(order) - 1

    def notifyRemoved(self, id):
        """ see interfaces.py """
        order = self._order()
        pos = self._pos()
        idx = pos[id]
        del order[idx]
        # we now need to rebuild pos since the ids have shifted
        pos.clear()
        for n, id in enumerate(order):
            pos[id] = n

    def moveObjectsByDelta(self, ids, delta, subset_ids=None,
            suppress_events=False):
        """ see interfaces.py """
        order = self._order()
        pos = self._pos()
        min_position = 0
        if isinstance(ids, basestring):
            ids = [ids]
        if subset_ids is None:
            subset_ids = self.idsInOrder()
        elif not isinstance(subset_ids, list):
            subset_ids = list(subset_ids)
        if delta > 0:                   # unify moving direction
            ids = reversed(ids)
            subset_ids.reverse()
        counter = 0
        for id in ids:
            try:
                old_position = subset_ids.index(id)
            except ValueError:
                continue
            new_position = max(old_position - abs(delta), min_position)
            if new_position == min_position:
                min_position += 1
            if not old_position == new_position:
                subset_ids.remove(id)
                subset_ids.insert(new_position, id)
                counter += 1
        if counter > 0:
            if delta > 0:
                subset_ids.reverse()
            idx = 0
            for i in range(len(order)):
                if order[i] in subset_ids:
                    id = subset_ids[idx]
                    try:
                        order[i] = id
                        pos[id] = i
                        idx += 1
                    except KeyError:
                        raise ValueError('No object with id "%s" exists.' % id)
        if not suppress_events:
            notifyContainerModified(self.context)
        return counter

    def moveObjectsUp(self, ids, delta=1, subset_ids=None):
        """ see interfaces.py """
        return self.moveObjectsByDelta(ids, -delta, subset_ids)

    def moveObjectsDown(self, ids, delta=1, subset_ids=None):
        """ see interfaces.py """
        return self.moveObjectsByDelta(ids, delta, subset_ids)

    def moveObjectsToTop(self, ids, subset_ids=None):
        """ see interfaces.py """
        return self.moveObjectsByDelta(ids, -len(self._order()), subset_ids)

    def moveObjectsToBottom(self, ids, subset_ids=None):
        """ see interfaces.py """
        return self.moveObjectsByDelta(ids, len(self._order()), subset_ids)

    def moveObjectToPosition(self, id, position, suppress_events=False):
        """ see interfaces.py """
        delta = position - self.getObjectPosition(id)
        if delta:
            return self.moveObjectsByDelta(id, delta,
                suppress_events=suppress_events)

    def orderObjects(self, key=None, reverse=None):
        """ see interfaces.py """
        if key is None and not reverse:
            return -1
        order = self._order()
        pos = self._pos()

        if key is None and reverse:
            # Simply reverse the current ordering.
            order.reverse()
        else:
            def keyfn(id):
                attr = getattr(self.context._getOb(id), key)
                if callable(attr):
                    return attr()
                return attr
            order.sort(None, keyfn, bool(reverse))

        for n, id in enumerate(order):
            pos[id] = n
        return -1

    def getObjectPosition(self, id):
        """ see interfaces.py """
        pos = self._pos()
        if id in pos:
            return pos[id]
        else:
            raise ValueError('No object with id "%s" exists.' % id)

    def idsInOrder(self):
        """ see interfaces.py """
        return list(self._order())

    def __getitem__(self, index):
        return self._order()[index]

    # Annotation lookup with lazy creation

    def _order(self, create=False):
        annotations = IAnnotations(self.context)
        if create:
            return annotations.setdefault(self.ORDER_KEY, PersistentList())
        else:
            return annotations.get(self.ORDER_KEY, [])

    def _pos(self, create=False):
        annotations = IAnnotations(self.context)
        if create:
            return annotations.setdefault(self.POS_KEY, OIBTree())
        else:
            return annotations.get(self.POS_KEY, {})
