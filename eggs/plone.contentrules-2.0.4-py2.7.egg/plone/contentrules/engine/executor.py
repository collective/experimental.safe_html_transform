from zope.interface import implements
from zope.component import adapts, getMultiAdapter

from plone.contentrules.engine.interfaces import IRuleExecutor
from plone.contentrules.engine.interfaces import IRuleAssignable
from plone.contentrules.engine.interfaces import IRuleAssignmentManager

from plone.contentrules.engine.interfaces import StopRule

from plone.contentrules.rule.interfaces import IExecutable

class RuleExecutor(object):
    """An object that can execute rules in its context.
    """

    implements(IRuleExecutor)
    adapts(IRuleAssignable)

    def __init__(self, context):
        self.context = context

    def __call__(self, event, bubbled=False, rule_filter=None):
        assignments = IRuleAssignmentManager(self.context)
        for rule in assignments.getRules(event, bubbled=bubbled):
            # for each rule assigned in this context - bubbled means rule apply on subfolders
            if rule_filter is None or rule_filter(self.context, rule, event) == True:
                # execute the rule if it is not filtered, for exemple,
                # it has not been executed on the same content but from an other context
                # in the same request

                # we store cascading option in the filter. if true, this will allow
                # rules to be executed because of the actions ran by this rule.
                if rule_filter is not None:
                    cascade_before = getattr(rule_filter, 'cascade', False)
                    rule_filter.cascade = rule.cascading

                executable = getMultiAdapter((self.context, rule, event), IExecutable)
                executable()
               
                if rule_filter is not None:
                    rule_filter.cascade = cascade_before

                if rule.stop:
                    # stop rule execution if 'Stop rules after' option has been selected
                    raise StopRule(rule)
