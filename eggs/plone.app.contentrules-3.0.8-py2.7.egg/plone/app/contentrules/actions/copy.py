from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from zope.component import adapts
from zope.event import notify
from zope.formlib import form
from zope.interface import implements, Interface
from zope.lifecycleevent import ObjectCopiedEvent
from zope import schema

from Acquisition import aq_base
import OFS.subscribers
from OFS.event import ObjectClonedEvent
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


class ICopyAction(Interface):
    """Interface for the configurable aspects of a move action.

    This is also used to create add and edit forms, below.
    """

    target_folder = schema.Choice(title=_(u"Target folder"),
                                  description=_(u"As a path relative to the portal root."),
                                  required=True,
                                  source=SearchableTextSourceBinder({'is_folderish': True},
                                                                    default_query='path:'))


class CopyAction(SimpleItem):
    """The actual persistent implementation of the action element.
    """
    implements(ICopyAction, IRuleElementData)

    target_folder = ''
    element = 'plone.actions.Copy'

    @property
    def summary(self):
        return _(u"Copy to folder ${folder}.",
                 mapping=dict(folder=self.target_folder))


class CopyActionExecutor(object):
    """The executor for this action.
    """
    implements(IExecutable)
    adapts(Interface, ICopyAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        portal_url = getToolByName(self.context, 'portal_url', None)
        if portal_url is None:
            return False

        obj = self.event.object

        path = self.element.target_folder
        if len(path) > 1 and path[0] == '/':
            path = path[1:]
        target = portal_url.getPortalObject().unrestrictedTraverse(str(path), None)

        if target is None:
            self.error(obj, _(u"Target folder ${target} does not exist.", mapping={'target': path}))
            return False

        try:
            obj._notifyOfCopyTo(target, op=0)
        except ConflictError:
            raise
        except Exception, e:
            self.error(obj, str(e))
            return False

        old_id = obj.getId()
        new_id = self.generate_id(target, old_id)

        orig_obj = obj
        obj = obj._getCopy(target)
        obj._setId(new_id)

        notify(ObjectCopiedEvent(obj, orig_obj))

        target._setObject(new_id, obj)
        obj = target._getOb(new_id)
        obj.wl_clearLocks()

        obj._postCopy(target, op=0)

        OFS.subscribers.compatibilityCall('manage_afterClone', obj, obj)

        notify(ObjectClonedEvent(obj))

        return True

    def error(self, obj, error):
        request = getattr(self.context, 'REQUEST', None)
        if request is not None:
            title = utils.pretty_title_or_id(obj, obj)
            message = _(u"Unable to copy ${name} as part of content rule 'copy' action: ${error}",
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


class CopyAddForm(AddForm):
    """An add form for move-to-folder actions.
    """
    form_fields = form.FormFields(ICopyAction)
    form_fields['target_folder'].custom_widget = UberSelectionWidget
    label = _(u"Add Copy Action")
    description = _(u"A copy action can copy an object to a different folder.")
    form_name = _(u"Configure element")

    def create(self, data):
        a = CopyAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class CopyEditForm(EditForm):
    """An edit form for copy rule actions.

    Formlib does all the magic here.
    """
    form_fields = form.FormFields(ICopyAction)
    form_fields['target_folder'].custom_widget = UberSelectionWidget
    label = _(u"Edit Copy Action")
    description = _(u"A copy action can copy an object to a different folder.")
    form_name = _(u"Configure element")
