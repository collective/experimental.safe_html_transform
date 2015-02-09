from persistent import Persistent
from z3c.objpath.interfaces import IObjectPath
from z3c.relationfield.interfaces import IRelationValue
from z3c.relationfield.interfaces import ITemporaryRelationValue
from zope import component
from zope.intid.interfaces import IIntIds
from zope.interface import Declaration
from zope.interface import implements
from zope.interface import providedBy


class RelationValue(Persistent):
    implements(IRelationValue)

    _broken_to_path = None

    def __init__(self, to_id):
        self.to_id = to_id
        # these will be set automatically by events
        self.from_object = None
        self.__parent__ = None
        self.from_attribute = None

    @property
    def from_id(self):
        intids = component.getUtility(IIntIds)
        return intids.getId(self.from_object)

    @property
    def from_path(self):
        return _path(self.from_object)

    @property
    def from_interfaces(self):
        return providedBy(self.from_object)

    @property
    def from_interfaces_flattened(self):
        return _interfaces_flattened(self.from_interfaces)

    @property
    def to_object(self):
        return _object(self.to_id)

    @property
    def to_path(self):
        if self.to_object is None:
            return self._broken_to_path
        return _path(self.to_object)

    @property
    def to_interfaces(self):
        return providedBy(self.to_object)

    @property
    def to_interfaces_flattened(self):
        return _interfaces_flattened(self.to_interfaces)

    def __eq__(self, other):
        if not isinstance(other, RelationValue):
            return False
        self_sort_key = self._sort_key()
        other_sort_key = other._sort_key()
        # if one of the relations we are comparing doesn't have a source
        # yet, only compare targets. This is to make comparisons within
        # ChoiceWidget work; a stored relation would otherwise not compare
        # equal with a relation generated for presentation in the UI
        if self_sort_key[0] is None or other_sort_key[0] is None:
            return self_sort_key[-1] == other_sort_key[-1]
        # otherwise do a full comparison
        return self_sort_key == other_sort_key

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if other is None:
            return cmp(self._sort_key(), None)
        return cmp(self._sort_key(), other._sort_key())

    def _sort_key(self):
        return (self.from_attribute, self.from_path, self.to_path)

    def broken(self, to_path):
        self._broken_to_path = to_path
        self.to_id = None

    def isBroken(self):
        return self.to_id is None


class TemporaryRelationValue(Persistent):
    """A relation that isn't fully formed yet.

    It needs to be finalized afterwards, when we are sure all potential
    target objects exist.
    """
    implements(ITemporaryRelationValue)

    def __init__(self, to_path):
        self.to_path = to_path

    def convert(self):
        return create_relation(self.to_path)


def _object(id):
    if id is None:
        return None
    intids = component.getUtility(IIntIds)
    try:
        return intids.getObject(id)
    except KeyError:
        # XXX catching this error is not the right thing to do.
        # instead, breaking a relation by removing an object should
        # be caught and the relation should be adjusted that way.
        return None


def _path(obj):
    if obj is None:
        return ''
    object_path = component.getUtility(IObjectPath)
    return object_path.path(obj)


def _interfaces_flattened(interfaces):
    return Declaration(*interfaces).flattened()


def create_relation(to_path):
    """Create a relation to a particular path.

    Will create a broken relation if the path cannot be resolved.
    """
    object_path = component.getUtility(IObjectPath)
    try:
        to_object = object_path.resolve(to_path)
        intids = component.getUtility(IIntIds)
        return RelationValue(intids.getId(to_object))
    except ValueError:
        # create broken relation
        result = RelationValue(None)
        result.broken(to_path)
        return result
