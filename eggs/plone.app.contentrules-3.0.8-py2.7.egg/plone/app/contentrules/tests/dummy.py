from OFS.SimpleItem import SimpleItem
from zope.interface import implements
from plone.contentrules.rule.interfaces import IRuleElementData
from zope.component.interfaces import IObjectEvent
from plone.uuid.interfaces import IAttributeUUID


class DummyCondition(SimpleItem):
    implements(IRuleElementData)
    element = "dummy.condition"
    summary = "Dummy condition"


class DummyAction(SimpleItem):
    implements(IRuleElementData)
    element = "dummy.action"
    summary = "Dummy action"


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, object):
        self.object = object


class DummyRule(object):

    def __init__(self, name='dummy'):
        self.__name__ = name


class DummyNonArchetypesContext(object):
    implements(IAttributeUUID)
