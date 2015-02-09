from persistent import Persistent

from OFS.Uninstalled import BrokenClass
from ZODB.broken import PersistentBroken
from zope.interface import implements, implementer
from zope.component import adapter, queryUtility
from zope.annotation.interfaces import IAnnotations
from zope.container.ordered import OrderedContainer
from zope.container.contained import Contained
from zope.container.interfaces import IObjectAddedEvent

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.engine.interfaces import IRuleAssignable
from plone.contentrules.engine.interfaces import IRuleAssignment
from plone.contentrules.engine.interfaces import IRuleAssignmentManager

from BTrees.OOBTree import OOBTree


def check_rules_with_dotted_name_moved(rule):
    """Migrate on-the-fly added event dotted name
    if Plone has been migrated from any release to 4.3 release.
    Avoids any upgrade to fail when setup profile is re-imported.
    """
    if PersistentBroken in rule.event.__bases__ or BrokenClass in rule.event.__bases__:
        if rule.event.__name__ == 'IObjectAddedEvent':
            rule.event = IObjectAddedEvent

KEY = 'plone.contentrules.localassignments'

class RuleAssignment(Contained, Persistent):
    """An assignment of a rule to a context
    """
    implements(IRuleAssignment)

    def __init__(self, ruleid, enabled=True, bubbles=False):
        super(RuleAssignment, self).__init__()
        self.__name__ = ruleid
        self.enabled = enabled
        self.bubbles = bubbles

class RuleAssignmentManager(OrderedContainer):
    """A context-specific container for rule assignments
    """
    implements(IRuleAssignmentManager)

    def __init__(self):
        # XXX: This depends on implementation detail in OrderedContainer,
        # but it uses a PersistentDict, which sucks :-/
        OrderedContainer.__init__(self)
        self._data = OOBTree()

    def getRules(self, event, bubbled=False):
        rules = []
        storage = queryUtility(IRuleStorage)
        if storage is not None:
            for a in self.values():
                if not a.enabled:
                    continue
                if not (bubbled == False or a.bubbles):
                    continue

                r = storage.get(a.__name__, None)
                if r is None:
                    continue

                try:
                    provided = r.event.providedBy(event)
                except AttributeError:
                    check_rules_with_dotted_name_moved(r)
                    provided = r.event.providedBy(event)

                if provided and r.enabled:
                    rules.append(r)

        return rules

@adapter(IRuleAssignable)
@implementer(IRuleAssignmentManager)
def ruleAssignmentManagerAdapterFactory(context):
    """When adapting an IRuleAssignable, get an IRuleAssignmentManager by
    finding one in the object's annotations. The container will be created
    if necessary.
    """
    annotations = IAnnotations(context)
    manager = annotations.get(KEY, None)
    if manager is None:
        manager = annotations[KEY] = RuleAssignmentManager()

    return manager
