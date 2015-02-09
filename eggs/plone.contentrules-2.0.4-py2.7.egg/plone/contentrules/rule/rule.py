from persistent import Persistent
from persistent.list import PersistentList

from zope.interface import implements, Interface
from zope.component import adapts, getMultiAdapter

from plone.contentrules.rule.interfaces import IRule
from plone.contentrules.rule.interfaces import IExecutable

class Rule(Persistent):
    """A rule.
    """

    implements(IRule)

    title = u''
    description = u''
    event = None
    enabled = True
    stop = False
    cascading = False

    __name__ = None
    __parent__ = None

    def __init__(self):
        self.conditions = PersistentList()
        self.actions = PersistentList()

class RuleExecutable(object):
    """An adapter capable of executing a rule
    """

    implements(IExecutable)
    adapts(Interface, IRule, Interface)

    def __init__(self, context, rule, event):
        self.context = context
        self.rule = rule
        self.event = event

    def __call__(self):
        for condition in self.rule.conditions:
            executable = getMultiAdapter((self.context, condition, self.event), IExecutable)
            if not executable():
                return False
        for action in self.rule.actions:
            executable = getMultiAdapter((self.context, action, self.event), IExecutable)
            if not executable():
                return False
        return True
