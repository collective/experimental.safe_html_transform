from zope.interface import implements

from plone.z3cform.fieldsets.interfaces import IGroupFactory
from plone.z3cform.fieldsets.interfaces import IDescriptiveGroup

from z3c.form import group

class Group(group.Group):
    implements(IDescriptiveGroup)

    __name__ = u""
    label = u""
    description = u""

    def getContent(self):
        # Default to sharing content with parent
        return self.__parent__.getContent()

class GroupFactory(object):
    implements(IGroupFactory)

    def __init__(self, __name__, fields, label=None, description=None):
        self.__name__ = __name__
        self.fields = fields

        self.label = label or __name__
        self.description = description

    def __call__(self, context, request, parentForm):
        g = Group(context, request, parentForm)
        g.__name__ = self.__name__
        g.label = self.label
        g.description = self.description
        g.fields = self.fields
        return g
