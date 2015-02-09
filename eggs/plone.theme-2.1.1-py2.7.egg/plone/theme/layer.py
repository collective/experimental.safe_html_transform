from zope.interface import directlyProvides, directlyProvidedBy
from zope.component import queryUtility

from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from Products.CMFCore.utils import getToolByName
from plone.theme.interfaces import IDefaultPloneLayer

default_layers = [
    IDefaultPloneLayer,
    IDefaultBrowserLayer,
    ]

try:
    from Products.CMFDefault.interfaces import ICMFDefaultSkin
except ImportError:
    pass
else:
    default_layers.append(ICMFDefaultSkin)


def mark_layer(site, event):
    """Mark the request with a layer corresponding to the current skin,
    as set in the portal_skins tool.
    """
    if getattr(event.request, "_plonetheme_", False):
        return
    event.request._plonetheme_=True

    portal_skins = getToolByName(site, 'portal_skins', None)
    if portal_skins is not None:
        skin_name = site.getCurrentSkinName()
        skin = queryUtility(IBrowserSkinType, name=skin_name)
        if skin is not None:
            layer_ifaces = []
            default_ifaces = []
            # We need to make sure IDefaultPloneLayer comes after
            # any other layers, even if they don't explicitly extend it.
            if IDefaultPloneLayer in skin.__iro__:
                default_ifaces += [IDefaultPloneLayer]
            for layer in directlyProvidedBy(event.request):
                if layer in default_layers:
                    default_ifaces.append(layer)
                elif IBrowserSkinType.providedBy(layer):
                    continue
                else:
                    layer_ifaces.append(layer)
            ifaces = [skin, ] + layer_ifaces + default_ifaces
            directlyProvides(event.request, *ifaces)
