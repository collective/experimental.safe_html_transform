from zope.interface import implements
from plone.folder.interfaces import IOrderable


class DummyObject(object):

    def __init__(self, id, meta_type=None):
        self.id = id
        self.meta_type = meta_type

    def __of__(self, obj):
        return self

    def manage_fixupOwnershipAfterAdd(self):
        pass

    def dummy_method(self):
        return self.id


class Orderable(DummyObject):
    """ orderable mock object """
    implements(IOrderable)


class Chaoticle(DummyObject):
    """ non-orderable mock object;  this does not implement `IOrderable` """
