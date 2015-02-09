from zope.component import queryUtility
from plone.contentrules.engine.assignments import RuleAssignment
from plone.contentrules.engine.interfaces import IRuleStorage,\
    IRuleAssignmentManager
from plone.app.contentrules.rule import get_assignments, insert_assignment


def assign_rule(container, rule_id, enabled=True, bubbles=True,
                insert_before=None):
    """Assign
       @param string rule_id
       rule to
       @param object container
    with options
       @param bool enabled
       @param bool bubbles (apply in subfolders)
       @param string insert-before
    """
    storage = queryUtility(IRuleStorage)
    if storage is None:
        return

    assignable = IRuleAssignmentManager(container, None)
    if assignable is None:
        return

    assignment = assignable.get(rule_id, None)
    if assignment is None:
        assignable[rule_id] = RuleAssignment(rule_id)

    assignable[rule_id].enabled = bool(enabled)
    assignable[rule_id].bubbles = bool(bubbles)
    path = '/'.join(container.getPhysicalPath())
    insert_assignment(storage[rule_id], path)

    if insert_before:
        position = None
        keys = list(assignable.keys())
        if insert_before == "*":
            position = 0
        elif insert_before in keys:
            position = keys.index(insert_before)

        if position is not None:
            keys.remove(rule_id)
            keys.insert(position, rule_id)
            assignable.updateOrder(keys)


def unassign_rule(container, rule_id):
    """Remove
       @param string rule_id
       rule from
       @param object container
    """
    assignable = IRuleAssignmentManager(container)
    storage = queryUtility(IRuleStorage)
    path = '/'.join(container.getPhysicalPath())
    del assignable[rule_id]
    get_assignments(storage[rule_id]).remove(path)


def edit_rule_assignment(container, rule_id, bubbles=None, enabled=None):
    """Change a property of an assigned rule
    @param object container
    @param string rule_id
    @param bool enabled
    @param bool bubbles (apply in subfolders)
    """
    assignable = IRuleAssignmentManager(container)
    assignment = assignable.get(rule_id, None)
    if bubbles is not None:
        assignment.bubbles = bool(bubbles)

    if enabled is not None:
        assignment.enabled = bool(enabled)
