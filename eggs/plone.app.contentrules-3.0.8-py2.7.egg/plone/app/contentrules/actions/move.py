from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from zope.component import adapts
from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.formlib import form
from zope.interface import implements, Interface
from zope.lifecycleevent import ObjectMovedEvent
from zope import schema

from Acquisition import aq_inner, aq_parent, aq_base
from OFS.event import ObjectWillBeMovedEvent
from OFS.CopySupport import sanity_check
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


class IMoveAction(Interface):
    """Interface for the configurable aspects of a move action.

    This is also used to create add and edit forms, below.
    """

    target_folder = schema.Choice(title=_(u"Target folder"),
                                  description=_(u"As a path relative to the portal root."),
                                  required=True,
                                  source=SearchableTextSourceBinder({'is_folderish': True},
                                                                    default_query='path:'))


class MoveAction(SimpleItem):
    """The actual persistent implementation of the action element.
    """
    implements(IMoveAction, IRuleElementData)

    target_folder = ''
    element = 'plone.actions.Move'

    @property
    def summary(self):
        return _(u"Move to folder ${folder}", mapping=dict(folder=self.target_folder))


class MoveActionExecutor(object):
    """The executor for this action.
    """
    implements(IExecutable)
    adapts(Interface, IMoveAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        portal_url = getToolByName(self.context, 'portal_url', None)
        if portal_url is None:
            return False

        obj = self.event.object
        parent = aq_parent(aq_inner(obj))

        path = self.element.target_folder
        if len(path) > 1 and path[0] == '/':
            path = path[1:]
        target = portal_url.getPortalObject().unrestrictedTraverse(str(path), None)

        if target is None:
            self.error(obj, _(u"Target folder ${target} does not exist.", mapping={'target': path}))
            return False

        if target.absolute_url() == parent.absolute_url():
            # We're already here!
            return True

        try:
            obj._notifyOfCopyTo(target, op=1)
        except ConflictError:
            raise
        except Exception, e:
            self.error(obj, str(e))
            return False

        # Are we trying to move into the same container that we copied from?
        if not sanity_check(target, obj):
            return False

        old_id = obj.getId()
        new_id = self.generate_id(target, old_id)

        notify(ObjectWillBeMovedEvent(obj, parent, old_id, target, new_id))

        obj.manage_changeOwnershipType(explicit=1)

        try:
            parent._delObject(old_id, suppress_events=True)
        except TypeError:
            # BBB: removed in Zope 2.11
            parent._delObject(old_id)

        obj = aq_base(obj)
        obj._setId(new_id)

        try:
            target._setObject(new_id, obj, set_owner=0, suppress_events=True)
        except TypeError:
            # BBB: removed in Zope 2.11
            target._setObject(new_id, obj, set_owner=0)
        obj = target._getOb(new_id)

        notify(ObjectMovedEvent(obj, parent, old_id, target, new_id))
        notifyContainerModified(parent)
        if aq_base(parent) is not aq_base(target):
            notifyContainerModified(target)

        obj._postCopy(target, op=1)

        # try to make ownership implicit if possible
        obj.manage_changeOwnershipType(explicit=0)

        return True

    def error(self, obj, error):
        request = getattr(self.context, 'REQUEST', None)
        if request is not None:
            title = utils.pretty_title_or_id(obj, obj)
            message = _(u"Unable to move ${name} as part of content rule 'move' action: ${error}",
                          mapping={'name': title, 'error': error})
            IStatusMessage(request).addStatusMessage(message, type="error")

    def generate_id(self, target, old_id):
        taken = getattr(aq_base(target), 'has_key', None)
        if taken is None:
            item_ids = set(target.objectIds())
            taken = lambda x: x in item_ids
        if not taken(old_id):
            return old_id
        idx = 1
        while taken("%s.%d" % (old_id, idx)):
            idx += 1
        return "%s.%d" % (old_id, idx)


class MoveAddForm(AddForm):
    """An add form for move-to-folder actions.
    """
    form_fields = form.FormFields(IMoveAction)
    form_fields['target_folder'].custom_widget = UberSelectionWidget
    label = _(u"Add Move Action")
    description = _(u"A move action can move an object to a different folder.")
    form_name = _(u"Configure element")

    def create(self, data):
        a = MoveAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class MoveEditForm(EditForm):
    """An edit form for move rule actions.

    Formlib does all the magic here.
    """
    form_fields = form.FormFields(IMoveAction)
    form_fields['target_folder'].custom_widget = UberSelectionWidget
    label = _(u"Edit Move Action")
    description = _(u"A move action can move an object to a different folder.")
    form_name = _(u"Configure element")
