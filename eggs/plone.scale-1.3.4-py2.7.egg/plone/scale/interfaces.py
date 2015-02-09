from zope.interface import Interface


class IScaledImageQuality(Interface):
    """Marker interface for utility query.

    This can be used by plone.app.imaging to define a property "scaled image
    quality" in the site's image handling settings.

    The property can then be used in plone.namedfile as well as in
    Products.Archetypes and Products.ATContentTypes (the latter two currently
    by a patch in plone.app.imaging.monkey).
    """
