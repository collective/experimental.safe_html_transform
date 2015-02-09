from interfaces import ITestObject
from zope.interface import alsoProvides as mark

def dummy(kdict, name='dummy', iface=ITestObject, bases=(object,)):
    """ factory for dummies """
    obj = type(name, bases, kdict)()
    mark(obj, iface)
    return obj

def getToolByName(context, tool_name):
    """
    acquisition faker
    """
    return getattr(context, tool_name)

portal_path = "/path_to/portal"

class portal_url(object):
    def __init__(self, portal_path=portal_path):
        self.portal_path=portal_path

    def getPortalPath(self):
        return self.portal_path

_marker = object()
class pdo(dict):
    """
    pseudo data object....masquerades as a brain
    """

    def __init__(self, **kwargs):
        self.update(kwargs)

    def __getattr__(self, key):
        ret = self.get(key, _marker)
        if not ret is _marker:
            return ret
        raise AttributeError

    def getPath(self):
        return portal_path + "/%s" %self.getId

    def getObject(self):
        self.UID = lambda : self.UID
        return self
