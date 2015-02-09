from zope.interface import alsoProvides

from zope.component import queryUtility
from zope.component import getSiteManager
from zope.component import getAllUtilitiesRegisteredFor

from plone.browserlayer.interfaces import ILocalBrowserLayerType


def register_layer(layer, name, site_manager=None):
    """Register the given layer (an interface) with the given name. If it is
    already registered, nothing will be done. If site_manager is not given,
    the current site manager will be used.
    """

    existing = queryUtility(ILocalBrowserLayerType, name=name)
    if existing is not None:
        return

    if site_manager is None:
        site_manager = getSiteManager()

    if not ILocalBrowserLayerType.providedBy(layer):
        alsoProvides(layer, ILocalBrowserLayerType)

    site_manager.registerUtility(component=layer,
                                 provided=ILocalBrowserLayerType,
                                 name=name)


def unregister_layer(name, site_manager=None):
    """Unregister the layer with the given name. If it cannot be found, a
    KeyError is raised.
    """

    existing = queryUtility(ILocalBrowserLayerType, name=name)
    if existing is None:
        raise KeyError("No browser layer with name %s is registered." % name)

    if site_manager is None:
        site_manager = getSiteManager()

    site_manager.unregisterUtility(component=existing,
                                   provided=ILocalBrowserLayerType,
                                   name=name)


def registered_layers():
    """Return all currently registered layers
    """
    return getAllUtilitiesRegisteredFor(ILocalBrowserLayerType)
