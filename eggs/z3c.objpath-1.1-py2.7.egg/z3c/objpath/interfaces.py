from zope.interface import Interface

class IObjectPath(Interface):
    """Path representation for objects.
    """
    def path(obj):
        """Give the path representation of obj.

        obj - object in a hierarchy of IContainer objects.

        The path is defined by the application and may be relative
        to the application root.

        Returns the path.
        
        If no path to the object can be made, raise a ValueError.
        """

    def resolve(path):
        """Given a path resolve to an object.

        path - a path as created with path()

        Returns the object that the path referred to.

        If the path cannot be resolved to an object, raise a ValueError.
        """
