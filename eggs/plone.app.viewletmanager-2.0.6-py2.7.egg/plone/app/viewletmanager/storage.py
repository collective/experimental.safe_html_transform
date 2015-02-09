from zope.interface import implements

from persistent import Persistent
from persistent.dict import PersistentDict

from plone.app.viewletmanager.interfaces import IViewletSettingsStorage


class ViewletSettingsStorage(Persistent):
    implements(IViewletSettingsStorage)

    def __init__(self):
        self._order = PersistentDict()
        self._hidden = PersistentDict()
        self._defaults = PersistentDict()

    def getOrder(self, name, skinname):
        skin = self._order.get(skinname, {})
        order = skin.get(name, ())
        if not order:
            skinname = self.getDefault(name)
            if skinname is not None:
                skin = self._order.get(skinname, {})
                order = skin.get(name, ())
        return order

    def setOrder(self, name, skinname, order):
        skin = self._order.setdefault(skinname, PersistentDict())
        skin[name] = tuple(order)
        if self.getDefault(name) is None:
            self.setDefault(name, skinname)

    def getHidden(self, name, skinname):
        skin = self._hidden.get(skinname, {})
        hidden = skin.get(name, ())
        if not hidden:
            skinname = self.getDefault(name)
            if skinname is not None:
                skin = self._hidden.get(skinname, {})
                hidden = skin.get(name, ())
        return hidden

    def setHidden(self, name, skinname, hidden):
        skin = self._hidden.setdefault(skinname, PersistentDict())
        skin[name] = tuple(hidden)

    def getDefault(self, name):
        try:
            return self._defaults.get(name)
        except AttributeError:  # Backward compatibility
            self._defaults = PersistentDict()
            self.setDefault(name, 'Plone Default')
            return self.getDefault(name)

    def setDefault(self, name, skinname):
        try:
            self._defaults[name] = skinname
        except AttributeError:  # Backward compatibility
            self._defaults = PersistentDict()
            self.setDefault(name, skinname)
