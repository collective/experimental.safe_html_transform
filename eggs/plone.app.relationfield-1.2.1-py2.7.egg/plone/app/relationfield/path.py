from zope.interface import implements
from z3c.objpath.interfaces import IObjectPath

try:
    from zope.component.hooks import getSite
except ImportError:
    from zope.app.component.hooks import getSite
from zExceptions import NotFound


class Zope2ObjectPath(object):
    """Path representation for Zope 2 objects.
    """
    
    implements(IObjectPath)
    
    def path(self, obj):
        try:
            return '/'.join(obj.getPhysicalPath())
        except AttributeError:
            raise ValueError(obj)

    def resolve(self, path):
        site = getSite()
        if site is None:
            raise ValueError(path)
        
        try:
            root = site.getPhysicalRoot()
        except AttributeError:
            raise ValueError(path)
        
        try:
            return root.unrestrictedTraverse(path)
        except (AttributeError, NotFound, KeyError):
            raise ValueError(path)
