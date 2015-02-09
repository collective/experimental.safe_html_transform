from zope.interface import Interface


class IViewletSettingsStorage(Interface):
    """Stores settings for viewlets, like order and visibility."""

    def getOrder(name, skinname):
        """Returns tuple with ordered names of viewlets for the given
           viewletmanager (name) and skin name."""

    def setOrder(name, skinname, order):
        """Takes the tuple of names from ``order`` and stores it for the
           given viewletmanager (name) and skin name."""

    def getHidden(name, skinname):
        """Returns tuple with names of hidden viewlets for the given
           viewletmanager (name) and skin name."""

    def setHidden(name, skinname, hidden):
        """Takes the tuple of names from ``hidden`` and stores it for the
           given viewletmanager (name) and skin name."""


class IViewletManagementView(Interface):
    pass
