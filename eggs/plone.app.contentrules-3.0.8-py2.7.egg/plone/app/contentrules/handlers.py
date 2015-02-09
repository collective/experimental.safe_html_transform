import threading

from zope.component import queryUtility
from zope.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent,\
    IContainerModifiedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.interface import Interface
from zope.component.hooks import getSite

from plone.app.discussion.interfaces import IComment
from plone.contentrules.rule.interfaces import IRule
from plone.contentrules.engine.interfaces import IRuleExecutor
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.engine.interfaces import StopRule

from Acquisition import aq_inner, aq_parent
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces import ISiteRoot, IContentish
from Products.CMFCore.utils import getToolByName
from Products.ZCTextIndex.interfaces import IZCLexicon
from AccessControl.userfolder import UserFolder

try:
    from Products.Archetypes.interfaces import IBaseObject
    from Products.Archetypes.interfaces import IObjectInitializedEvent
    HAS_ARCHETYPES = True
except ImportError:
    class IBaseObject(Interface):
        pass
    class IObjectInitializedEvent(Interface):
        pass
    HAS_ARCHETYPES = False


def _get_uid(context):
    uid = IUUID(context, None)
    if uid is not None:
        return uid

    try:
        return '/'.join(context.getPhysicalPath())
    except AttributeError:
        pass

    try:
        return context.id
    except AttributeError:
        return ''


class DuplicateRuleFilter(object):
    """A filter which can prevent rules from being executed more than once
    regardless of context.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.executed = set()
        self.in_progress = False
        self.cascade = False

    def __call__(self, context, rule, event):
        exec_context = getattr(event, 'object', context)
        uid = _get_uid(exec_context)
        if (uid, rule.__name__, ) in self.executed:
            return False
        else:
            self.executed.add((uid, rule.__name__, ))
            return True

# A thread local for keeping track of rule execution across events
_status = threading.local()


def init():
    if not hasattr(_status, 'rule_filter'):
        _status.rule_filter = DuplicateRuleFilter()
    if not hasattr(_status, 'delayed_events'):
        _status.delayed_events = {}


def close(event):
    """Close the event processing when the request ends
    """
    if hasattr(_status, 'rule_filter'):
        _status.rule_filter.reset()

    if hasattr(_status, 'delayed_events'):
        _status.delayed_events = {}


def execute(context, event):
    """Execute all rules relative to the context, and bubble as appropriate.
    """
    # Do nothing if there is no rule storage or it is not active
    storage = queryUtility(IRuleStorage)
    if storage is None or not storage.active:
        return

    init()

    rule_filter = _status.rule_filter

    # Stop if someone else is already executing. This could happen if,
    # for example, a rule triggered here caused another event to be fired.
    # We continue if we are in the context of a 'cascading' rule.

    if rule_filter.in_progress and not rule_filter.cascade:
        return

    # Tell other event handlers to be equally kind
    rule_filter.in_progress = True

    # Prepare to break hard if a rule demanded execution be stopped
    try:

        # Try to execute rules in the context. It may not work if the context
        # is not a rule executor, but we may still want to bubble events
        executor = IRuleExecutor(context, None)
        if executor is not None:
            executor(event, bubbled=False, rule_filter=rule_filter)

        # Do not bubble beyond the site root
        if not ISiteRoot.providedBy(context):
            parent = aq_parent(aq_inner(context))
            while parent is not None:
                executor = IRuleExecutor(parent, None)
                if executor is not None:
                    executor(event, bubbled=True, rule_filter=rule_filter)
                if ISiteRoot.providedBy(parent):
                    parent = None
                else:
                    parent = aq_parent(aq_inner(parent))

    except StopRule:
        pass

    # We are done - other events that occur after this one will be allowed to
    # execute rules again
    rule_filter.in_progress = False


# Event handlers


def is_portal_factory(context):
    """Find out if the given object is in portal_factory
    """
    portal_factory = getToolByName(context, 'portal_factory', None)
    if portal_factory is not None:
        return portal_factory.isTemporary(context)
    else:
        return False


def execute_rules(event):
    """ When an action is invoked on an object,
        execute rules assigned to its parent.
        Base action executor handler """
    if is_portal_factory(event.object):
        return

    execute(aq_parent(aq_inner(event.object)), event)


def added(event):
    """When an object is added, execute rules assigned to its new parent.

    There is special handling for Archetypes objects.
    """
    obj = event.object
    if is_portal_factory(obj):
        return

    # The object added event executes too early for Archetypes objects.
    # We need to delay execution until we receive a subsequent
    # IObjectInitializedEvent
    if IBaseObject.providedBy(obj):
        init()
        _status.delayed_events['IObjectInitializedEvent-%s' % _get_uid(obj)] = event
    elif IContentish.providedBy(obj) or IComment.providedBy(obj):
        execute(event.newParent, event)
    else:
        return


if HAS_ARCHETYPES:
    def archetypes_initialized(event):
        """Pick up the delayed IObjectAddedEvent when an Archetypes object is
        initialised.
        """
        obj = event.object
        if is_portal_factory(obj):
            return

        if not IBaseObject.providedBy(obj):
            return

        init()
        delayed_event = _status.delayed_events.get(
                               'IObjectInitializedEvent-%s' % _get_uid(obj), None)
        if delayed_event is not None:
            _status.delayed_events['IObjectInitializedEvent-%s' % _get_uid(obj)] = None
            execute(delayed_event.newParent, delayed_event)


def removed(event):
    """When an IObjectRemovedEvent was received, execute rules assigned to its
     previous parent.
    """
    obj = event.object
    if not (IContentish.providedBy(obj) or IComment.providedBy(obj)):
        return

    if is_portal_factory(obj):
        return

    execute(event.oldParent, event)


def modified(event):
    """When an object is modified, execute rules assigned to its parent
    """

    obj = event.object
    if not (IContentish.providedBy(obj) or IComment.providedBy(obj)):
        return

    # Let the special handler take care of IObjectInitializedEvent
    for event_if in (IObjectInitializedEvent, IObjectAddedEvent,
        IObjectRemovedEvent, IContainerModifiedEvent, IObjectCopiedEvent):
        if event_if.providedBy(event):
            return

    execute_rules(event)


def copied(event):
    """When an object is copied, execute rules assigned to its parent
    """
    obj = event.object
    if not (IContentish.providedBy(obj) or IComment.providedBy(obj)):
        return

    if is_portal_factory(obj):
        return

    execute(aq_parent(aq_inner(event.original)), event)


def workflow_action(event):
    """When a workflow action is invoked on an object, execute rules assigned
    to its parent.
    """
    execute_rules(event)


def execute_user_rules(event):
    site = getSite()
    execute(site, event)


def user_created(event):
    """When a user has been created, execute rules assigned to the Plonesite.
    """
    execute_user_rules(event)


def user_logged_in(event):
    """When a user is logged in, execute rules assigned to the Plonesite.
    """
    execute_user_rules(event)


def user_logged_out(event):
    """When a user is logged out, execute rules assigned to the Plonesite.
    """
    execute_user_rules(event)
