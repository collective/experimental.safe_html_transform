from zope.component.zcml import utility
from zope.interface import Interface

from plone.contentrules.rule.interfaces import IRuleCondition, IRuleAction
from plone.contentrules.rule.element import RuleCondition, RuleAction

def ruleConditionDirective(_context, name, title, addview, editview=None,
        description="", for_=Interface, event=Interface, schema=None, factory=None):
    """Register a utility for IRuleCondition based on the parameters in the
    zcml directive
    """

    condition = RuleCondition()
    condition.title = title
    condition.addview = addview
    condition.editview = editview
    condition.description = description
    condition.for_ = for_
    condition.event = event
    condition.schema = schema
    condition.factory = factory

    utility(_context, provides=IRuleCondition, component=condition, name=name)


def ruleActionDirective(_context, name, title, addview, editview=None,
    description="", for_=Interface, event=Interface, schema=None, factory=None):
    """Register a utility for IRuleAction based on the parameters in the
    zcml directive
    """

    action = RuleAction()
    action.title = title
    action.addview = addview
    action.editview = editview
    action.description = description
    action.for_ = for_
    action.event = event
    action.schema = schema
    action.factory = factory

    utility(_context, provides=IRuleAction, component=action, name=name)
