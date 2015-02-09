from zope.interface import implements, Interface

from plone.contentrules.rule.interfaces import IRuleElement, IRuleCondition, IRuleAction

class RuleElement(object):
    """A rule element.

    Ordinarily, rule elements will be created via ZCML directives, which will
    register them as utilities.
    """

    implements(IRuleElement)

    title = u''
    description = u''
    for_ = Interface
    event = None
    addview = None
    editview = None
    schema = None
    factory = None

class RuleCondition(RuleElement):
    """A rule condition.

    Rule conditions are just rule elements, but are registered under a more
    specific interface to enable the UI to differentate between different types
    of elements.
    """
    implements(IRuleCondition)

class RuleAction(RuleElement):
    """A rule action.

    Rule action are just rule elements, but are registered under a more
    specific interface to enable the UI to differentate between different types
    of elements.
    """
    implements(IRuleAction)
