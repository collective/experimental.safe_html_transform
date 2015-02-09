from zope.interface import Interface, Attribute
from zope import schema

from zope.container.interfaces import IContained
from zope.container.interfaces import IOrderedContainer
from zope.container.interfaces import IContainerNamesContainer

from zope.container.constraints import contains
from zope.annotation.interfaces import IAttributeAnnotatable

class StopRule(Exception):
    """An event that informs us that rule execution should be aborted.
    """

    def __init__(self, rule):
        self.rule = rule

class IRuleStorage(IOrderedContainer, IContainerNamesContainer):
    """A storage for rules. This is registered as a local utility.
    """
    contains('plone.contentrules.rule.interfaces.IRule')

    active = schema.Bool(title=u"Rules in this storage are active")

class IRuleAssignable(IAttributeAnnotatable):
    """Marker interface for objects that can be assigned rules
    """

class IRuleAssignment(IContained):
    """An assignment of a rule to a context
    """

    __name__ = schema.TextLine(title=u"The id of the rule")

    enabled = schema.Bool(title=u"Whether or not the rule is currently enabled")
    bubbles = schema.Bool(title=u"Whether or not the rule will apply to objects in subfolders")

class IRuleAssignmentManager(IOrderedContainer):
    """An object that is capable of being assigned rules.

    Normally, an object will be adapted to IRuleAssignmentManager in order
    to manipulate the rule assignments in this location.
    """

    def getRules(event, bubbled=False):
        """Get all enabled rules registered for the given event and
        assigned to this context. If bubbled is True, only rules that are
        bubbleable will be returned.
        """

class IRuleExecutor(Interface):
    """An object that is capable of executing rules.

    Typically, a content object will be adapted to this interface
    """

    def __call__(event, bubbled=False, rule_filter=None):
        """Execute all rules applicable in the current context

        event is the triggering event. bubbled should be True if the rules
        are being executed as part of a bubbling up of events (i.e. this
        is a parent of the context where the event was triggered). filter,
        if given, is a callable that will be passed each rule in turn and
        can vote on whether it should be executed by returning True or
        False. It should take the arguments (context, rule, event).
        """
