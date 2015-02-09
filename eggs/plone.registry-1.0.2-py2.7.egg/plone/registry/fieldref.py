from zope.interface import implementedBy
from zope.interface import implements

from plone.registry.interfaces import IFieldRef

class FieldRef(object):
    """Default field reference.
    """

    implements(IFieldRef)

    def __init__(self, name, originalField):
        self.recordName = name
        self.originalField = originalField

    @property
    def __providedBy__(self):
        provided = getattr(self, '__provides__', None)
        if provided is None:
            provided = implementedBy(self.__class__)

        return provided + self.originalField.__providedBy__

    def __getattr__(self, name):
        return getattr(self.originalField, name)
