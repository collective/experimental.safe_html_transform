from plone.theme.interfaces import IDefaultPloneLayer

class IThemeSpecific(IDefaultPloneLayer):
    """Marker interface that defines a Zope browser layer.
       If you need to register a viewlet only for the
       "Plone Classic Theme" theme, this interface must be its layer.
    """

class ILegacyThemeSpecific(IThemeSpecific):
    """Marker interface for the "Old Plone 3 Custom Theme" skin that is
       created when upgrading the "Plone Default" skin from Plone 3, to make
       sure it continues to get the old viewlet order.
    """