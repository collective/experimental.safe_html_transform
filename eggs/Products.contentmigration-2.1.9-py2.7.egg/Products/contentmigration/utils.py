"""Utility functions."""

from cgi import escape
import sys
import warnings

from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.lifecycleevent import ObjectMovedEvent

from Acquisition import aq_base, aq_inner, aq_parent
from App.Dialogs import MessageDialog
from OFS.event import ObjectWillBeMovedEvent
from OFS.CopySupport import sanity_check, CopyError
from OFS.CopySupport import eNotSupported
from ZODB.POSException import ConflictError


def unrestricted_move(self, ob):
    """Move an object from one container to another bypassing certain
    checks."""
    orig_id = ob.getId()
    if not ob.cb_isMoveable():
        raise CopyError(eNotSupported % escape(orig_id))

    try:
        ob._notifyOfCopyTo(self, op=1)
    except ConflictError:
        raise
    except:
        raise CopyError(MessageDialog(
            title="Move Error",
            message=sys.exc_info()[1],
            action='manage_main'))

    if not sanity_check(self, ob):
        raise CopyError("This object cannot be pasted into itself")

    orig_container = aq_parent(aq_inner(ob))
    if aq_base(orig_container) is aq_base(self):
        id = orig_id
    else:
        id = self._get_id(orig_id)

    notify(ObjectWillBeMovedEvent(ob, orig_container, orig_id,
                                  self, id))

    # try to make ownership explicit so that it gets carried
    # along to the new location if needed.
    ob.manage_changeOwnershipType(explicit=1)

    try:
        orig_container._delObject(orig_id, suppress_events=True)
    except TypeError:
        # BBB: removed in Zope 2.11
        orig_container._delObject(orig_id)
        warnings.warn(
            "%s._delObject without suppress_events is deprecated "
            "and will be removed in Zope 2.11." %
            orig_container.__class__.__name__, DeprecationWarning)
    ob = aq_base(ob)
    ob._setId(id)

    try:
        self._setObject(id, ob, set_owner=0, suppress_events=True)
    except TypeError:
        # BBB: removed in Zope 2.11
        self._setObject(id, ob, set_owner=0)
        warnings.warn(
            "%s._setObject without suppress_events is deprecated "
            "and will be removed in Zope 2.11." %
            self.__class__.__name__, DeprecationWarning)
    ob = self._getOb(id)

    notify(ObjectMovedEvent(ob, orig_container, orig_id, self, id))
    notifyContainerModified(orig_container)
    if aq_base(orig_container) is not aq_base(self):
        notifyContainerModified(self)

    ob._postCopy(self, op=1)
    # try to make ownership implicit if possible
    ob.manage_changeOwnershipType(explicit=0)


def getSavedAttrName(attrName):
    return '_old_%s' % attrName


def patch(context, originalAttrName, replacement):
    """ Default handler that preserves original method """
    OLD_NAME = getSavedAttrName(originalAttrName)
    if not hasattr(context, OLD_NAME):
        setattr(context, OLD_NAME, getattr(context, originalAttrName))
    setattr(context, originalAttrName, replacement)


def undoPatch(context, originalAttrName):
    OLD_NAME = getSavedAttrName(originalAttrName)
    setattr(context, originalAttrName, getattr(context, OLD_NAME))
    delattr(context, OLD_NAME)
