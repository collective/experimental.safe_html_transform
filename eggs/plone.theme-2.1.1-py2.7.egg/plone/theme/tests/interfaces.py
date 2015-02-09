# A browser layer - you should make one of these for your own skin
# and register it with a name corresponding to a skin in portal_skins.
# See tests.zcml and README.txt for more.

from plone.theme.interfaces import IDefaultPloneLayer


class IMyTheme(IDefaultPloneLayer):
    """Marker interface used in the tests
    """
